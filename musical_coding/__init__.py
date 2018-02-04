"""MusicalCoding.

Convert any piece of code to its musical representation.
"""

import collections
import logging

from docopt import docopt
import fluidsynth
import numpy
import pyaudio
import pygments
import pygments.lexers
import soundfile

SFILE = '/usr/share/sounds/sf2/FluidR3_GM.sf2'

logging.basicConfig(level=logging.DEBUG)


class Adjust:
    """Adjust."""

    max_num = 7

    @classmethod
    def adjust_note(cls, value):
        return (value * 5)

    @classmethod
    def adjust_duration(cls, value):
        result = int(value / 10)
        if result > 10:
            result = result / 10
        if result < 2:
            result = 1
        return result


class MusicalCodeFile:
    """MUsical Code File."""

    def __init__(self, filename, values=None, sfile=SFILE, freq=44100,
                 adjust_class=Adjust):
        self.file = open(filename).readlines()
        self.freq = freq
        self.lexer = pygments.lexers.guess_lexer_for_filename(
            filename, self.file)

        if not values:
            values = {'Token.Keyword': 0.1, 'Token.Text': 0.2,
                      'Token.Punctuation': 0.01, 'Token.Name.Function': 0.1}
        self.token_values = collections.defaultdict(lambda: 0, values)
        self.fluid = fluidsynth.Synth()
        sfid = self.fluid.sfload(sfile)
        self.adjust = adjust_class
        self.fluid.program_select(0, sfid, 0, 0)

    def note_for_line(self, line):
        """Notes."""
        return round(sum([self.token_values[str(a[0])] * len(a[1])
                          for a in pygments.lex(line, self.lexer)]))

    @property
    def notes(self):
        """Notes."""
        for line in self.file:
            yield (self.adjust.adjust_note(self.note_for_line(line)),
                   self.adjust.adjust_duration(len(line)), line)

    def play(self):
        pa = pyaudio.PyAudio()
        strm = pa.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=self.freq,
            output=True)
        audio = self.audio
        print("Got audio, playing.")
        strm.write(audio)

    @property
    def numpy_array(self):
        """To numpy arrays."""
        curr = []
        for note, duration, line in self.notes:
            logging.debug("line <<<%s>>> produced note %s duration %s",
                          line, note, duration)
            duration = self.freq * duration
            self.fluid.noteon(0, note * 10, 30)
            curr = numpy.append(curr, self.fluid.get_samples(duration))
            self.fluid.noteoff(0, note * 10)
        return curr

    @property
    def audio(self):
        return fluidsynth.raw_audio_string(self.numpy_array)

    def save(self, location):
        return soundfile.write(location, self.numpy_array, self.freq)

    @classmethod
    def postprocess(cls, value):
        return value


def main():
    """musical_coding.

    Convert any piece of code to its musical representation.

    Usage: musical_coding [options]

    Options:
        --verbose          Enable verbose mode
        --file=<file>      File to render from
        --output=<file>    File to render to, if not provided, stdout
    """
    options = docopt(main.__doc__)
    if not options['--output']:
        MusicalCodeFile(options['--file']).play()
    else:
        MusicalCodeFile(options['--file']).save(options['--output'])
