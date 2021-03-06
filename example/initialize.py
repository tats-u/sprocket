#!/usr/bin/env python

"""An example script to initialize audio lists and speaker configurations.

Usage: initialize.py [-h] [-1] [-2] [-3] SOURCE TARGET SAMPLING_RATE

Options:
    -h, --help     Show the help
    -1, --step1    Execute step1 (Generation of initial list files)
    -2, --step2    Execute step2 (Generation of configure files)
    -3, --step3    Execute step3 (Estimation of F0 ranges)
    SOURCE         The name of speaker
                   whose voice you would like to convert from
    TARGET         The name of speaker whose voice you would like to convert to
    SAMPLING_RATE  The sampling rate of WAV files of voices
"""

from __future__ import division  # , unicode_literals
from __future__ import absolute_import, print_function

import os
import shutil
import sys

import six
from docopt import docopt

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))  # isort:skip
from src import initialize_speaker  # isort:skip # pylint: disable=C0413


def create_configure(dest, base, exist_ok=True):
    """Creates a configuration file based on a template file.

    This does not overwrite the existing one.

    Parameters
    ----------
    dest : str or path-like
        The path of the configuration file you are creating.
    base : str or path-like
        The path of the template configure file.
    exist_ok : bool
        If `False`, this function throws
        `IOError` (Python 2.7) or `FileExistsError` (Python 3 or later)
        when `dest` is already created.

    Raises
    ------
    IOError (Python 2.7) or FileExistsError (Python 3 or later)
        If `exist_ok` is `False` and `dest` is already exists.
        You can catch both of them by:
        >>> except IOError:
    """
    if os.path.exists(dest):
        message = "The configuration file {} already exists.".format(dest)
        if exist_ok:
            print(message)
        else:
            raise (IOError if six.PY2 else FileExistsError)(message)
    else:
        print("Generate {}".format(dest), file=sys.stderr)
        shutil.copy(base, dest)


def create_list(dest, wav_dir, exist_ok=True):
    """Create an audio list file based on a template.

    This does not overwrite the existing one.

    Parameters
    ----------
    dest : str or path-like
        The path of the list file you are creating.
    wav_dir : str or path-like
        The path of the directory of audio files.
        The name of directory must be that of speaker.
    exist_ok : bool
        If `False`, this function throws
        `IOError` (Python 2.7) or `FileExistsError` (Python 3 or later)
        when `dest` is already created.

    Raises
    ------
    IOError (Python 2.7) or FileExistsError (Python 3 or later)
        If `exist_ok` is `False` and `dest` is already exists.
        You can catch both of them by:
        >>> except IOError:

    Notes
    -----
    List example of the speaker `SPEAKER`::

        SPEAKER/001
        SPEAKER/002
        SPEAKER/003

    when there is a audio directory of him/her named `SPEAKER` that contains:
        * 001.wav
        * 002.wav
        * 003.wav
        * other_file.txt (ignored)
    Note that the delimiter `/` turns to `\\` in Windows.
    """
    if os.path.exists(dest):
        message = "The list file {} already exists.".format(dest)
        if exist_ok:
            print(message)
        else:
            raise (IOError if six.PY2 else FileExistsError)(message)
    else:
        print("Generate {}".format(dest))
        speaker_label = os.path.basename(wav_dir)
        lines = (os.path.join(speaker_label, os.path.splitext(wav_file_name)[0])
                 for wav_file_name in os.listdir(wav_dir)
                 if os.path.splitext(wav_file_name)[1] == ".wav")
        with open(dest, "w") as file_handler:
            for line in sorted(lines):
                print(line, file=file_handler)


LIST_EXTENSION = ".list"
USES = ("train", "eval")
LIST_SUFFIXES = {
    use: "_" + use + LIST_EXTENSION for use in USES}
YML_EXTENSION = ".yml"

EXAMPLE_ROOT_DIR = os.path.dirname(__file__)
CONF_DIR = os.path.join(EXAMPLE_ROOT_DIR, "conf")
DATA_DIR = os.path.join(EXAMPLE_ROOT_DIR, "data")
LIST_DIR = os.path.join(EXAMPLE_ROOT_DIR, "list")
WAV_DIR = os.path.join(DATA_DIR, "wav")

if __name__ == "__main__":
    args = docopt(__doc__)  # pylint: disable=invalid-name
    LABELS = {label: args[label.upper()] for label in ("source", "target")}
    SOURCE_TARGET_PAIR = LABELS["source"] + "-" + LABELS["target"]
    PAIR_DIR = os.path.join(DATA_DIR, "pair",
                            SOURCE_TARGET_PAIR)
    LIST_FILES = {
        speaker_part: {
            use: os.path.join(LIST_DIR, speaker_label + LIST_SUFFIXES[use])
            for use in USES}
        for speaker_part, speaker_label in LABELS.items()}
    SPEAKER_CONF_FILES = {
        part: os.path.join(
            CONF_DIR, "speaker", label + YML_EXTENSION)
        for part, label in LABELS.items()}
    PAIR_CONF_FILE = os.path.join(
        CONF_DIR, "pair", SOURCE_TARGET_PAIR + YML_EXTENSION)
    SAMPLING_RATE = args["SAMPLING_RATE"]

    # The first False is dummy for alignment
    #   between indexes of `args_execute_steps` and arguments
    # pylint: disable=invalid-name
    execute_steps = [False] \
        + [args["--step{}".format(step_index)] for step_index in range(1, 4)]

    # Execute all steps if no options on steps are given
    # Keep index #0 False in case you create a hotbed for bugs.
    if not any(execute_steps):
        raise("Please specify steps with options")

    if execute_steps[1]:
        print("### 1. create initial list files ###")
        # create list files for both the speakers
        for use in USES:
            for part, speaker in LABELS.items():
                create_list(LIST_FILES[part][use],
                            os.path.join(WAV_DIR, speaker))
        print("# Please modify train and eval list files, if you want. #")

    if execute_steps[2]:
        print("### 2. create configure files ###")
        # create speaker-dependent configure file
        for part, speaker in LABELS.items():
            create_configure(
                SPEAKER_CONF_FILES[part],
                os.path.join(
                    CONF_DIR, "default",
                    "speaker_default_{}{}".format(
                        SAMPLING_RATE, YML_EXTENSION)))
        # create pair-dependent configure file
        create_configure(PAIR_CONF_FILE, os.path.join(
            CONF_DIR, "default", "pair_default.yml"))

    if execute_steps[3]:
        print("### 3. create figures to define F0 range ###")
        # get F0 range in each speaker
        for part, speaker in LABELS.items():
            initialize_speaker.main(
                speaker, LIST_FILES[part]["train"],
                WAV_DIR, os.path.join(CONF_DIR, "figure"))
        print("# Please modify f0 range values"
              " in speaker-dependent YAML files based on the figure #")
