"""MusicalCoding.

Convert any piece of code to its musical representation.
"""

from functools import lru_cache
import logging

from docopt import docopt
import fluidsynth
import numpy
import pyaudio
import tokenize
import soundfile

# SFILE = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
SFILE = "/usr/share/sounds/sf2/TimGM6mb.sf2"

logging.basicConfig(level=logging.DEBUG)


class MusicalCodeFile:
    """MUsical Code File."""

    max_num = 7

    def __init__(self, filename, sfile=SFILE, freq=44100, max_note_speed=5,
                 start_note=10, start_duration=0):
        self.start_note = start_note
        self.start_duration = start_duration
        self.file = open(filename).readlines()
        self.freq = freq
        self.fluid = fluidsynth.Synth()
        sfid = self.fluid.sfload(sfile)
        self.tokens = list(tokenize.generate_tokens(open(filename).readline))
        self.maxsize = max([len(a.string) for a in self.tokens])
        self.midsize = int(self.maxsize * 0.55)
        if self.midsize > max_note_speed:
            self.midsize = max_note_speed
        logging.debug("Max note duration: %s", self.midsize)
        self.fluid.program_select(0, sfid, 0, 0)
        self.note_speed = 20

    def adjust_note(cls, value):
        if value > 100:
            value -= 100
        elif value < 40:
            value += 20
        return int(value)

    def adjust_duration(self, value):
        result = value / 2

        if result > self.midsize:
            while result > self.midsize:
                result -= self.midsize

        if result == 0:
            result = 0.3

        return result

    @property
    @lru_cache()
    def notes(self):
        """Notes."""
        note = self.start_note
        value = self.start_duration
        line = ''
        for token in self.tokens:
            if token.string == '\n':
                yield (self.adjust_note(note),
                       self.adjust_duration(value),
                       line)
                note = 0
                value = 0
                line = ''
            else:
                note += token.type
                value += len(token.string)
                line += ' ' + token.string

    def audio_stream(self):
        """Get audio stream."""
        pa = pyaudio.PyAudio()
        return pa.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=self.freq,
            output=True)

    def play(self):
        self.audio_stream().write(self.audio)

    @property
    @lru_cache()
    def numpy_array(self):
        """To numpy arrays."""
        curr = []
        curr_notes = []
        pending_notes = []
        for note, duration, line in self.notes:
            logging.debug("line <<<%s>>> produced note %s duration %s",
                          line, note, duration)

            # If duration is less than three, we assume it's a background one.
            if duration <= 0.3:
                pending_notes.append((0, note, int(self.note_speed / 2)))
            else:
                curr_notes.append((0, note, self.note_speed))
                # May add some curr_notes logic here too
                for note_a in curr_notes:
                    self.fluid.noteon(*note_a)
                    for note in pending_notes:
                        # Maybe remove too-close octaves?
                        self.fluid.noteon(*note)

                    pending_notes = []

                    curr = numpy.append(
                        curr, self.fluid.get_samples(
                            int((self.freq * duration) / 2)))

                    self.fluid.noteoff(*note_a[:-1])

                    curr = numpy.append(
                        curr, self.fluid.get_samples(
                            int(self.freq * (duration / 2))))

                    for note in pending_notes:
                        self.fluid.noteoff(*note)

                curr_notes = []
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
