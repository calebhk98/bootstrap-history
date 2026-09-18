"""A save written with fog off must not load into a fogged game and
hand the player the whole tree.

Regrouped from test_round8_fixes.py - see CLAUDE.md's test-file
reorganisation note. Checks moved verbatim; the comment explains the break
it guards.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: a save written with the fog OFF loaded into a fogged game and
# handed the player the whole tree. The check has to run BEFORE the save's own
# fog flag is restored, or it validates the value it is about to reject.
_sv = "_fogtamper_test.json"          # saves must be relative paths
_svp = os.path.join(ROOT, _sv)
if os.path.exists(_svp):
    os.remove(_svp)
proto([{"cmd": "save", "file": _sv}])                       # written unfogged
_r8, _out8, _rc8 = proto([{"cmd": "load", "file": _sv}, {"cmd": "state"}],
                         fog=True)
check("a save played without fog cannot be loaded into a fogged game",
      any("fog" in json.dumps(x).lower() and x.get("ok") is False for x in _r8),
      _out8[:200])
check("...and refusing it does not kill the session", _rc8 == 0)
if os.path.exists(_svp):
    os.remove(_svp)
