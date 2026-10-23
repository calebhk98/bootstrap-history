"""Complaint 640: SavePolicy decides when a live process writes its --session file. Interval zero writes after every
command; a positive interval holds writes back until it has passed, except after a command that names a file or ends
the sitting or the game; leaving writes what was held back. Called with a clock and a recording writer."""
QUICK_TOPIC = True

from unittest import mock

from .harness import *  # noqa: F401,F403

from sim.ui import save_policy
from sim.ui.save_policy import SavePolicy


class _Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def policy_and_writes(session="game.json", interval=0.0, seconds_since_write=0.0):
    clock = _Clock()
    policy = SavePolicy(session, interval, clock=clock)
    policy.last_saved = clock.now - seconds_since_write
    return policy, []


def after(policy, writes, command, ended=False):
    """Whether the command was saved, with the writer recorded in `writes`."""
    with mock.patch.object(save_policy, "save_session", lambda game, path: writes.append(path)):
        return policy.after_command("game", command, ended=ended)


policy, writes = policy_and_writes(interval=0.0)
check("interval zero writes after the command", after(policy, writes, {"cmd": "state"}) is True and writes == ["game.json"], writes)

policy, writes = policy_and_writes(interval=3600.0)
check("a positive interval holds an ordinary command back", after(policy, writes, {"cmd": "state"}) is False and writes == []
      and policy.unsaved is True, (writes, policy.unsaved))
for name in sorted(save_policy.ALWAYS_SAVE_COMMANDS):
    policy, writes = policy_and_writes(interval=3600.0)
    check("...but writes after '%s', which names a file or ends the sitting" % name,
          after(policy, writes, {"cmd": name}) is True and policy.unsaved is False, (name, writes))
policy, writes = policy_and_writes(interval=3600.0)
check("...and writes when the game has ended", after(policy, writes, {"cmd": "step"}, ended=True) is True)
policy, writes = policy_and_writes(interval=3600.0, seconds_since_write=3599.0)
check("...and holds back just short of the interval", after(policy, writes, {"cmd": "state"}) is False and writes == [])
policy, writes = policy_and_writes(interval=3600.0, seconds_since_write=3601.0)
check("...and writes once the interval has passed since the last write", after(policy, writes, {"cmd": "state"}) is True and writes == ["game.json"])

policy, writes = policy_and_writes(interval=3600.0)
policy.unsaved = True
with mock.patch.object(save_policy, "save_session", lambda game, path: writes.append(path)):
    policy.flush("game")
check("leaving writes what was held back", writes == ["game.json"] and policy.unsaved is False, writes)
policy, writes = policy_and_writes(interval=3600.0)
with mock.patch.object(save_policy, "save_session", lambda game, path: writes.append(path)):
    policy.flush("game")
check("leaving with nothing held back writes nothing", writes == [])
policy, writes = policy_and_writes(session=None, interval=0.0)
check("a sitting with no session file writes nothing", after(policy, writes, {"cmd": "state"}) is False and writes == [])
