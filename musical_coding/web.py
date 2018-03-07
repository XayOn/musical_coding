"""Serve musweb app."""

import os
from pathlib import Path
import hashlib
import subprocess

from aiohttp.web import Application
import aiohttp.web
from docopt import docopt

from . import MusicalCodeFile


async def render_music(request):
    """Render music from code provided in request as a lilypond file."""
    text = await request.text()
    mfile = MusicalCodeFile.from_string(text)

    oformat = request.match_info.get('format', 'ly')
    nformat = oformat if oformat != "srt" else "mp4"
    headers = {'content-disposition': 'attachment; filename="music.{nformat}"'}

    md5hash = hashlib.sha256()
    md5hash.update(text.encode())
    output_dir = Path('/tmp') / md5hash.hexdigest()

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

    return aiohttp.web.Response(
        body=(output_dir / mfile).read_bytes(), headers=headers)


def run():
    """ musical_coding_web

    Usage: musical_coding [options]

    Options:

        --debug  Debug  [default: False]
        --host=<host>   Host to listen on  [default:0.0.0.0]
        --port=<port>   Port to listen on  [default:8080]

    """
    options = docopt(run.__doc__)
    app = Application(debug=options["--debug"])
    app.router.add_post('/{format}', render_music)
    app.router.add_post('/', render_music)
    aiohttp.web.run_app(
        app, host=options['--host'], port=int(options['--port']), print=False)
