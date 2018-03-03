""" Constants.

Basic definition, syntetizing piano.

TODO: Decide how to implement accords.
TODO: Add more instruments.
TODO: I have the score, now find a better way to represent it...
"""

from collections import namedtuple
from functools import lru_cache
from docopt import docopt
import fluidsynth
import numpy
import pyaudio
import soundfile
import tokenize

SFILE = "/usr/share/sounds/sf2/TimGM6mb.sf2"

ly_template = """
 \\score {{
  \\new Staff <<

    \\new Voice {{
      \\set midiInstrument = #"piano"
      \\voiceOne
      {notes}
    }}
  >>
  \\layout {{ }}
  \\midi {{}}
}}
"""

NOTES = {
    0: 60,  # A
    1: 68,  # B
    2: 76,  # C
    3: 82,  # D
    4: 90,  # E
    5: 98,  # F
    6: 116,  # G
}

NOTE_NAMES = {
    NOTES[0]: 'a',
    NOTES[1]: 'b',
    NOTES[2]: 'c',
    NOTES[3]: 'd',
    NOTES[4]: 'e',
    NOTES[5]: 'f',
    NOTES[6]: 'g',
}

SCALES = (1, 2, 3)

DURATIONS = (
    1,
    1 / 2,
    1 / 4,
    1 / 8,
    1 / 16,
    1 / 32,
    1 / 64,
)

DURATION_NAMES = {
    DURATIONS[0]: 1,
    DURATIONS[1]: 2,
    DURATIONS[2]: 4,
    DURATIONS[3]: 8,
    DURATIONS[4]: 16,
    DURATIONS[5]: 32,
    DURATIONS[6]: 64
}

SCALE_NAMES = {1: "'", 2: "''", 3: "'''", 4: "''''"}


class Note(namedtuple('Note', 'value, scale, duration, line')):
    def __repr__(self):
        return "{}{}{}".format(NOTE_NAMES[self.value], SCALE_NAMES[self.scale],
                               DURATION_NAMES[self.duration])


def get_normalized_note(max_note: Note, note: Note) -> Note:
    """Normalize a note."""

    def scale(old_value, old_max, new_max):
        """Scale."""
        return (old_value / old_max) * new_max

    value = NOTES[int(scale(note.value, max_note.value, len(NOTES) - 1))]
    scale_ = note.scale
    # SCALES[int(scale(note.scale, max_note.scale, len(SCALES) - 1))]
    duration = DURATIONS[int(
        scale(note.duration, max_note.duration,
              len(DURATIONS) - 1))]

    return Note(value, scale_, duration, note.line)


def get_tokenization(filename):
    note, value = 0, 0
    enum = enumerate(tokenize.generate_tokens(open(filename).readline))
    for num, token in enum:
        # TODO: A "strict" mode should be implemented that does not ignore
        # anything
        if token.line == '\n':
            # Avoid empty lines.
            continue
        if 'import' in token.line and num < 400:
            # ignore imports... they all sound equal and they're boring
            # at the song start
            continue
        if token.type == 3:
            # ingore docstrings, they're too large
            continue
        if token.string == '\n':
            yield note, 1, value, token.line
            note, value = 0, 0
        else:
            note += token.type
            value += len(token.string)


class MusicalCodeFile:
    """Musical Code File."""

    def __init__(self,
                 filename,
                 sfile=SFILE,
                 note_speed=20,
                 freq=44100,
                 speed_multiplier=0.8):
        self.freq = freq
        self.fluid = fluidsynth.Synth()
        sfid = self.fluid.sfload(sfile)
        self.fluid.program_select(0, sfid, 0, 0)
        self.note_speed = note_speed  # Note speed, as fluidsynth specifies
        self.speed_multiplier = speed_multiplier
        notes = list(Note(*args) for args in get_tokenization(filename))
        max_note = Note(
            max(note.value for note in notes),
            max(note.scale for note in notes),
            max(note.duration for note in notes), '')
        self.notes = list(
            get_normalized_note(max_note, note) for note in notes)

    def audio_stream(self):
        """Get audio stream."""
        pa = pyaudio.PyAudio()
        return pa.open(
            format=pyaudio.paInt16, channels=2, rate=self.freq, output=True)

    def play(self):
        self.audio_stream().write(self.audio)

    @property
    @lru_cache()
    def numpy_array(self):
        """To numpy arrays."""
        curr = []
        length = len(self.notes)
        for p, note in enumerate(self.notes):
            percent = "{:0.0f}%".format(numpy.ceil((p / length) * 100))
            print(percent, end='\033[20D', flush=True)
            self.fluid.noteon(0, note.value, self.note_speed)
            curr = numpy.append(
                curr,
                self.fluid.get_samples(
                    int((self.freq * note.duration * self.speed_multiplier))))
            self.fluid.noteoff(0, note.value)
        return curr

    def save_lilypond(self, where):
        with open(where, 'wb') as fileo:
            fileo.write(
                ly_template.format(notes='\n\t'.join(
                    str(a) for a in self.notes)))

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
        --verbose           Enable verbose mode
        --file=<file>       File to render from
        --output=<file>     File to render to, if not provided, stdout
        --output-ly=<file>  Write a lilypond file.
    """
    options = docopt(main.__doc__)
    mfile = MusicalCodeFile(options['--file'])
    if not options['--output']:
        mfile.play()
    else:
        mfile.save(options['--output'])
    if options['--output-ly']:
        mfile.save_lilypond(options['--output-ly'])
