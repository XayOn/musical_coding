"""Serve musweb app."""

from pathlib import Path
import hashlib
import itertools
import os
import subprocess

from aiohttp.web import Application
import aiohttp.web
from docopt import docopt
from git import Repo

from . import MusicalCodeFile

BASE = 'https://api.github.com/repos/{}'


def render_file(request, text, oformat):
    print(text)
    mfile = MusicalCodeFile.from_string(text)

    md5hash = hashlib.sha256()
    md5hash.update(text.encode())
    output_dir = Path(request.app['tmpdir']) / md5hash.hexdigest()

    if not output_dir.exists():
        os.makedirs(output_dir)
        (output_dir / 'music.ly').write_text(mfile.to_lilypond())
        (output_dir / 'music.srt').write_text(mfile.to_srt())
        subprocess.check_call(['lilypond', 'music.ly'], cwd=output_dir)

    wav = (output_dir / 'music.wav')
    if oformat in ('sub', 'mp4', 'wav') and not wav.exists():
        subprocess.check_call(
            ['timidity', '-Ow', '-o', 'music.wav', 'music.midi'],
            cwd=output_dir)

    mp4_output = (output_dir / 'music.mp4').exists()
    if oformat in ('sub', 'mp4') and not mp4_output:
        subprocess.check_call(
            [
                'ffmpeg', '-i', 'music.wav', '-filter_complex',
                '[0:a]avectorscope=s=480x480:zoom=4.5:rc=0:gc=200:'
                'bc=0:rf=0:gf=40:bf=0,format=yuv420p[v]; [v]'
                'pad=854:480:187:0[out]', '-map', '[out]', '-map', '0:a',
                '-b:v', '700k', '-b:a', '360k', '-strict', '-2', 'music.mp4'
            ],
            cwd=output_dir)

    mfile = 'music.{}'.format(oformat)

    if oformat == 'sub':
        subprocess.check_call(
            [
                'ffmpeg', '-i', 'music.mp4', '-f', 'srt', '-i', 'music.srt',
                '-map', '0:0', '-map', '0:1', '-map', '1:0', '-c:v', 'copy',
                '-c:a', 'copy', '-c:s', 'mov_text', 'music_sub.mp4'
            ],
            cwd=output_dir)
        mfile = 'music_sub.mp4'
    return (output_dir / mfile).read_bytes()


async def render_music(request):
    """Render music from code provided in request as a lilypond file."""
    oformat = request.match_info.get('format', 'ly')
    headers = {'content-disposition': 'attachment; filename="music.{nformat}"'}
    return aiohttp.web.Response(
        body=render_file(request, await request.text(), oformat),
        headers=headers)


def parse_files(root, files, output):
    """Find python files."""
    return [[root.replace(str(output.absolute()), '') + '/' + a] for a in files
            if a.endswith('.py')]


async def list_repository(request):
    """Clone from github repository and return a list of files."""
    req = await request.json()

    async with request.app['session'] as sess:
        # Clone repository
        md5hash = hashlib.sha256()
        md5hash.update(req['repo'].encode())
        digest = md5hash.hexdigest()
        output = Path(request.app['tmpdir']) / digest

        async with aiohttp.ClientSession() as sess:
            res = await sess.get(BASE.format(req['repo']))
            res = await res.json()
            if not output.exists():
                output.mkdir()
                Repo.clone_from(res['clone_url'], str(output))
            files = list(
                itertools.chain(
                    *(parse_files(root, files, output)
                      for root, _, files in os.walk(str(output.absolute())))))
            return aiohttp.web.json_response({
                'digest': digest,
                'files': files
            })


async def from_repository_file(request):
    """Musically encode a specific file from a repository."""
    req = await request.json()
    md5hash = hashlib.sha256()
    md5hash.update(req['repo'].encode())
    digest = md5hash.hexdigest()
    output = Path(request.app['tmpdir']) / digest
    filename = output / req['filename'].lstrip('/')
    print(filename)
    oformat = request.match_info.get('format', 'ly')
    headers = {'content-disposition': 'attachment; filename="music.{nformat}"'}
    return aiohttp.web.Response(
        body=render_file(request, filename.read_text(), oformat),
        headers=headers)


async def create_session(app):
    """Create app-wide client session."""
    app['session'] = aiohttp.ClientSession()


def run():
    """ musical_coding_web

    Usage: musical_coding [options]

    Options:

        --debug  Debug  [default: False]
        --host=<host>   Host to listen on  [default:0.0.0.0]
        --port=<port>   Port to listen on  [default:8080]
        --tmpdir=<dir>  Where to store files

    """
    options = docopt(run.__doc__)
    app = Application(debug=options["--debug"])
    app.router.add_post('/render/{format}', render_music)
    app.router.add_post('/render', render_music)
    app.router.add_post('/import_repo', list_repository)
    app.router.add_post('/from_repo/{format}', from_repository_file)
    app.on_startup.append(create_session)
    app['tmpdir'] = options['--tmpdir']
    aiohttp.web.run_app(
        app, host=options['--host'], port=int(options['--port']), print=False)
