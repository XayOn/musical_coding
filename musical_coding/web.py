"""Serve musweb app."""

import os
from pathlib import Path
import hashlib
import subprocess

from aiohttp.web import Application
import aiohttp.web
from docopt import docopt

from . import MusicalCodeFile

HEADERS = {'content-disposition': 'attachment; filename="music.ly"'}


async def render_music(request):
    """Render music from code provided in request as a lilypond file."""
    text = await request.text()
    response = MusicalCodeFile.from_string(text).to_lilypond()

    oformat = request.match_info.get('format')

    md5hash = hashlib.sha256()
    md5hash.update(text.encode())
    output_dir = Path('/tmp') / md5hash.hexdigest()

    if oformat and oformat != 'ly':
        if not output_dir.exists():
            os.makedirs(output_dir)
            (output_dir / 'music.ly').write_text(response)
            subprocess.check_call(['lilypond', 'music.ly'], cwd=output_dir)
            if oformat == 'wav':
                subprocess.check_call(
                    ['timidity', '-Ow', '-o', 'music.wav', 'music.midi'],
                    cwd=output_dir)
        response = (output_dir / f'music.{oformat}').read_bytes()
    return aiohttp.web.Response(body=response, headers=HEADERS)


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
