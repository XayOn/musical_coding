MusicalCoding
-----------------------------

.. image:: https://travis-ci.org/XayOn/musical_coding.svg?branch=master
    :target: https://travis-ci.org/XayOn/musical_coding

.. image:: https://coveralls.io/repos/github/XayOn/musical_coding/badge.svg?branch=master
 :target: https://coveralls.io/github/XayOn/musical_coding?branch=master

.. image:: https://badge.fury.io/py/musical_coding.svg
    :target: https://badge.fury.io/py/musical_coding

Convert any piece of code to its musical representation.

Supports score generation via lilypond and direct WAV writing.


.. image:: ./docs/score.png?raw=True


Usage
-----

::

    musical_coding.

    Convert any piece of code to its musical representation.

    Usage: musical_coding [options]

    Options:
        --verbose           Enable verbose mode
        --file=<file>       File to render from
        --output=<file>     File to render to, if not provided, stdout
        --output-ly=<file>  Write a lilypond file.


Distributing
------------

Distribution may be done in the usual setuptools way.
If you don't want to use pipenv, just use requirements.txt file as usual and
remove Pipfile, setup.py will auto-detect Pipfile removal and won't try to
update requirements.

Note that, to enforce compatibility between PBR and Pipenv, this updates the
tools/pip-requires and tools/test-requires files each time you do a *dist*
command

General notes
--------------

This package uses PBR and pipenv.
Pipenv can be easily replaced by a virtualenv by keeping requirements.txt
instead of using pipenv flow.
If you don't need, or you're not actually using git + setuptools distribution
system, you can enable PBR manual versioning by creating a METADATA file with
content like::

    Name: musical_coding
    Version: 0.0.1

Generating documentation
------------------------

This package contains a extra-requires section specifiying doc dependencies.
There's a special hook in place that will automatically install them whenever
we try to build its dependencies, thus enabling us to simply execute::

        pipenv run python setup.py build_sphinx

to install documentation dependencies and buildd HTML documentation in docs/build/


Passing tests
--------------

Running tests should always be done inside pipenv.
This package uses behave for TDD and pytest for unit tests, you can execute non-wip
tests and behavioral tests using::

        pipenv run python setup.py test

TODO
----

- Add a website with services to create music based on a github repository
- Create musical videos with both audimeter and the code currently "playing".
- Auto-Analize trending github repositories
- Add options to rate code based on its music
- Create badges for code musicality
