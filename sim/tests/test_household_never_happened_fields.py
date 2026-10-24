"""household_never_happened_fields: Complaints/55. "Never happened" is a declared None (or a real zero for a
counter), never an absent attribute read through getattr."""
QUICK_TOPIC = True

import re

from .harness import *  # noqa: F401,F403
from sim.engine.state import HouseholdState
from sim.engine.state_holdings import SeatProgressState

HOUSEHOLD_OWNED = {
    "insolvent_years": 0,
    "wage_hours_this_year": 0.0,
    "_said_deputies": 0,
    "last_withdrawal": None,
    "_said_near_limit": None,
    "_said_autoopen": None,
}
SCENARIO_OWNED = {"_said_scandal": 0, "_said_parallelism": None}
ALL_INITIAL = dict(HOUSEHOLD_OWNED, **SCENARIO_OWNED)

_household = HouseholdState(capital=1000.0)
_seat_progress = SeatProgressState()
for _name, _initial in ALL_INITIAL.items():
    _owner = _household if _name in HOUSEHOLD_OWNED else _seat_progress
    check("a fresh state declares %s as its initial value" % _name, getattr(_owner, _name) == _initial,
          getattr(_owner, _name))

# Guard: no getattr-with-default on these names anywhere in sim/.
_GUARDED = "|".join(ALL_INITIAL)
_PATTERN = re.compile(r"""getattr\([^()]*,\s*["'](%s)["']\s*,""" % _GUARDED)
_offenders = []
for _dir, _subdirs, _files in os.walk(os.path.join(ROOT, "sim")):
    for _file in _files:
        if not _file.endswith(".py") or _file.startswith("test_household_never_happened_fields"):
            continue
        _file_path = os.path.join(_dir, _file)
        with open(_file_path, encoding="utf-8") as _handle:
            for _number, _line in enumerate(_handle, 1):
                if _PATTERN.search(_line):
                    _offenders.append("%s:%d" % (os.path.relpath(_file_path, ROOT), _number))
check("no getattr(obj, name, default) on the never-happened fields anywhere in sim/",
      not _offenders, _offenders)
