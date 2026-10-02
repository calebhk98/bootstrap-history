"""household_never_happened_fields: Complaints/55. "Never happened" is a declared
None (or a real zero for a counter), never an absent attribute read through getattr."""
import re
from .harness import *  # noqa: F401,F403

HOUSEHOLD_OWNED = {
    "insolvent_years": 0,
    "wage_hours_this_year": 0.0,
    "_said_deputies": 0,
    "last_withdrawal": None,
    "_said_near_limit": None,
    "_said_autoopen": None,
}
SCENARIO_OWNED = {"_said_scandal": 0, "_said_parallelism": None}
EVENT_VALUES = {
    "insolvent_years": 3, "wage_hours_this_year": 12.5, "_said_deputies": 2,
    "last_withdrawal": 140, "_said_near_limit": True,
    "_said_autoopen": {"some_node": 141}, "_said_scandal": 2,
    "_said_parallelism": True,
}


def _owner(sim_obj, name):
    state = sim_obj.state
    return state.household if name in HOUSEHOLD_OWNED else state.scenario


def _round_trip(sim_obj, filename):
    path = os.path.join(ROOT, _rel(filename))
    S.save_state(sim_obj, path)
    fresh = sim(capital=1.0)
    S.load_state(fresh, path)
    return fresh


ALL_INITIAL = dict(HOUSEHOLD_OWNED, **SCENARIO_OWNED)

fresh_sim = sim(capital=1000.0)
for _name, _initial in ALL_INITIAL.items():
    check("a fresh household reads %s as its declared initial value" % _name,
          getattr(_owner(fresh_sim, _name), _name) == _initial,
          getattr(_owner(fresh_sim, _name), _name))
    if _name in HOUSEHOLD_OWNED:
        try:
            _via_household = getattr(fresh_sim.household, _name)
            _raised = False
        except AttributeError:
            _via_household, _raised = None, True
        check("Household facade returns %s without raising" % _name,
              not _raised and _via_household == _initial, _via_household)

_loaded = _round_trip(fresh_sim, "never_happened_fresh.json")
for _name, _initial in ALL_INITIAL.items():
    check("a save written before any event loads %s back as its initial value" % _name,
          getattr(_owner(_loaded, _name), _name) == _initial,
          getattr(_owner(_loaded, _name), _name))

event_sim = sim(capital=1000.0)
for _name, _value in EVENT_VALUES.items():
    setattr(_owner(event_sim, _name), _name, _value)
_loaded_events = _round_trip(event_sim, "never_happened_events.json")
for _name, _value in EVENT_VALUES.items():
    check("%s round-trips after its event has fired" % _name,
          getattr(_owner(_loaded_events, _name), _name) == _value,
          getattr(_owner(_loaded_events, _name), _name))

# Guard: no getattr-with-default on these names anywhere in sim/.
_GUARDED = "|".join(ALL_INITIAL)
_PATTERN = re.compile(r"""getattr\([^()]*,\s*["'](%s)["']\s*,""" % _GUARDED)
_offenders = []
for _dir, _subdirs, _files in os.walk(os.path.join(ROOT, "sim")):
    for _file in _files:
        if not _file.endswith(".py") or _file == "test_household_never_happened_fields.py":
            continue
        _file_path = os.path.join(_dir, _file)
        with open(_file_path, encoding="utf-8") as _handle:
            for _number, _line in enumerate(_handle, 1):
                if _PATTERN.search(_line):
                    _offenders.append("%s:%d" % (os.path.relpath(_file_path, ROOT), _number))
check("no getattr(obj, name, default) on the never-happened fields anywhere in sim/",
      not _offenders, _offenders)
