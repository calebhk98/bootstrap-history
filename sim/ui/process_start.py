"""The two ends of a one-command process (`agent` or `play`): no garbage collection while the game loads, and no
interpreter teardown when the command is done.

A process that loads a save builds millions of long-lived objects; collecting cycles while it does is wasted work, and
tearing the heap down at exit is more of it, since the save is already written and the OS reclaims the memory.
`simulator.py` stops the collector before its imports when it is started as one of these commands."""
import gc
import os
import sys

GAME_COMMANDS = ("agent", "play")


def is_game_process(argv=None):
    """Whether the script was started as a game command (`simulator.py agent ...`)."""
    arguments = sys.argv if argv is None else argv
    return len(arguments) > 1 and arguments[1] in GAME_COMMANDS


def loaded():
    """The game is loaded: what exists now is kept out of later collections and the collector runs again.
    Does nothing unless the script stopped it."""
    if not gc.isenabled():
        gc.freeze()
        gc.enable()


def finish(argv=None):
    """Called when the script's command has returned: flush the streams and leave without tearing the heap down."""
    if not is_game_process(argv):
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except (OSError, ValueError):
            pass
    os._exit(0)
