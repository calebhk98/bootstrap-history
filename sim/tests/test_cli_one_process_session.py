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


def policy_and_writes(session="game.json", interval=0.0):
    clock = _Clock()
    writes = []
    policy = SavePolicy(session, interval, clock=clock)
    return policy, clock, writes


def after(policy, writes, command, ended=False):
    """Whether the command was saved, with the writer recorded in `writes`."""
    with mock.patch.object(save_policy, "save_session", lambda game, path: writes.append(path)):
        return policy.after_command("game", command, ended=ended)


policy, clock, writes = policy_and_writes(interval=0.0)
results = [after(policy, writes, {"cmd": "state"}), after(policy, writes, {"cmd": "step"})]
check("interval zero writes after every command", results == [True, True] and writes == ["game.json"] * 2, (results, writes))

policy, clock, writes = policy_and_writes(interval=3600.0)
check("a positive interval holds an ordinary command back", after(policy, writes, {"cmd": "state"}) is False and writes == []
      and policy.unsaved is True, (writes, policy.unsaved))
for name in sorted(save_policy.ALWAYS_SAVE_COMMANDS):
    check("...but writes after '%s', which names a file or ends the sitting" % name,
          after(policy, writes, {"cmd": name}) is True and policy.unsaved is False, (name, writes))
check("...and writes when the game has ended", after(policy_and_writes(interval=3600.0)[0], writes, {"cmd": "step"}, ended=True) is True)
policy, clock, writes = policy_and_writes(interval=3600.0)
clock.now += 3599.0
early = after(policy, writes, {"cmd": "state"})
clock.now += 2.0
late = after(policy, writes, {"cmd": "state"})
check("...and writes once the interval has passed since the last write", (early, late) == (False, True) and len(writes) == 1, (early, late, writes))

policy, clock, writes = policy_and_writes(interval=3600.0)
after(policy, writes, {"cmd": "state"})
with mock.patch.object(save_policy, "save_session", lambda game, path: writes.append(path)):
    policy.flush("game")
    policy.flush("game")
check("leaving writes what was held back, once", writes == ["game.json"] and policy.unsaved is False, writes)
policy, clock, writes = policy_and_writes(interval=3600.0)
with mock.patch.object(save_policy, "save_session", lambda game, path: writes.append(path)):
    policy.flush("game")
check("leaving with nothing held back writes nothing", writes == [])
policy, clock, writes = policy_and_writes(session=None, interval=0.0)
check("a sitting with no session file writes nothing", after(policy, writes, {"cmd": "state"}) is False and writes == [])
