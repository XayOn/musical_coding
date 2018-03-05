""" Constants.

Basic definition, syntetizing piano.

TODO: Decide how to implement accords.
TODO: Add more instruments.
TODO: I have the score, now find a better way to represent it...
"""

from collections import namedtuple
from io import StringIO
import tokenize

from docopt import docopt

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
    #    1,
    1 / 2,
    1 / 4,
    1 / 8,
    1 / 16,
    1 / 32,
    1 / 64,
)

DURATION_NAMES = {
    #    DURATIONS[0]: 1,
    DURATIONS[0]: 2,
    DURATIONS[1]: 4,
    DURATIONS[2]: 8,
    DURATIONS[3]: 16,
    DURATIONS[4]: 32,
    DURATIONS[5]: 64
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


def get_tokenization(readline):
    note, value = 0, 0
    enum = enumerate(tokenize.generate_tokens(readline))
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

    def __init__(self, fileo):
        """Init.

        Arguments:

            fileo: File object to read tokens from
            sfile: SoundFont file
            note_sp: Note speed
            multiplier: Speed multiplier for note speed
        """
        notes = list(Note(*args) for args in get_tokenization(fileo))
        max_note = Note(
            max(note.value for note in notes),
            max(note.scale for note in notes),
            max(note.duration for note in notes), '')
        self.notes = list(
            get_normalized_note(max_note, note) for note in notes)

    def to_lilypond(self):
        return ly_template.format(notes='\n\t'.join(
            str(a) for a in self.notes))

    @staticmethod
    def from_string(string):
        fileo = StringIO()
        fileo.write(string)
        fileo.seek(0)
        return MusicalCodeFile(fileo.readline)

    @classmethod
    def postprocess(cls, value):
        return value


def main():
    """Convert any piece of code to its musical representation.

    Usage: musical_coding --output-ly=out_file --file=in_file [--verbose]
    """
    options = docopt(main.__doc__)
    mfile = MusicalCodeFile(open(options['--file']).readline)
    with open(options['--output-ly']) as fob:
        fob.write(mfile.to_lilypond())
