"""When a live `play` or `agent` process writes its --session file.

Interval zero saves after every command (the default). A positive interval saves
only when that many seconds have passed since the last write, and always on a
command that names a file or ends the sitting, on the game ending, and on leaving.
The save is the same either way: it holds whatever the game is when it is written.
"""
import time

from .memory import save_session

# commands after which the file must already be current
ALWAYS_SAVE_COMMANDS = frozenset({"save", "load", "quit"})


# typed words that act on the session file or leave the sitting
SESSION_WORDS = frozenset({"options", "option", "settings", "saves", "save", "load", "menu", "again", "restart"})


class SavePolicy:
    def __init__(self, session, interval_seconds=0.0, clock=time.monotonic):
        self.session = session
        self.interval_seconds = max(0.0, float(interval_seconds or 0.0))
        self.clock = clock
        self.last_saved = clock()
        self.unsaved = False

    def after_command(self, sim, cmd, ended=False):
        """Write the session if the policy says so; returns whether it did."""
        if not self.session:
            return False
        name = cmd.get("cmd") if isinstance(cmd, dict) else None
        due = (self.interval_seconds <= 0 or ended or name in ALWAYS_SAVE_COMMANDS
               or self.clock() - self.last_saved >= self.interval_seconds)
        if not due:
            self.unsaved = True
            return False
        self.write(sim)
        return True

    def write(self, sim):
        save_session(sim, self.session)
        self.last_saved = self.clock()
        self.unsaved = False

    def flush(self, sim):
        """Leaving: write anything still held back."""
        if self.session and self.unsaved:
            self.write(sim)
