"""The industrial dashboard's rules (Complaint 640: called on inputs built here; the dashboard on a whole game is
in test_industrial_dashboard_scenario): the `changes` window checks and the typed front end."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.refusal import cause_of
from sim.ui.proto.economy import _changes_baseline, _changes_moved, _parse_changes_years
from sim.ui.protocol import parse_typed as _PT2

# --- the `years` argument.
for _bad, _why in ((True, "bool"), (2.5, "fractional"), (0, "zero"), (-1, "negative"), ("many", "text"), (None, "missing")):
    _years, _error = _parse_changes_years(_bad)
    check("`changes years=%r` (%s) is refused, not silently coerced" % (_bad, _why),
          _years is None and _error["ok"] is False, (_years, _error))
check("a whole number of years is accepted", _parse_changes_years(5) == (5, None), _parse_changes_years(5))
check("a whole number given as a float is accepted", _parse_changes_years(3.0) == (3, None), _parse_changes_years(3.0))

# --- the window against the recorded history.
_history = [{"year": 100 + step} for step in range(6)]
_now, _baseline, _error = _changes_baseline([], 99, 105)
check("no history is refused rather than diffed against nothing", _now is None and _error["ok"] is False, _error)
_now, _baseline, _error = _changes_baseline(_history, 102, 105)
check("the baseline is the latest snapshot at or before the cutoff and now is the newest",
      _error is None and _baseline["year"] == 102 and _now["year"] == 105, (_now, _baseline, _error))
_now, _baseline, _error = _changes_baseline(_history, 95, 105)
check("a window older than the record is refused by name, saying how far back the record goes",
      _now is None and cause_of(_error["error"]) == "window_beyond_record" and _error["years_of_record"] == 5
      and _error["earliest_year"] == 100, _error)

# --- the deltas are one subtraction per tracked figure.
_snapshot = {"price_index": 1.0, "wage_index": 1.0, "literacy_general": 0.1, "literacy_elite": 0.5, "capital": 100.0,
             "revenue": 10.0, "credit_limit": 50.0, "employees_total": 3.0, "scholars": 1.0,
             "artisans": 2.0, "operating_count": 4, "done_earned": 10, "scandal": 0.0, "reputation": 1.0, "eminence": 0.5}
_later = dict(_snapshot, price_index=1.25, capital=160.0, revenue=5.0, done_earned=13)
_moved = _changes_moved(_snapshot, _later)
check("the moved figures are the later snapshot less the earlier",
      _moved["price_index"] == 0.25 and _moved["capital"] == 60.0 and _moved["revenue"] == -5.0
      and _moved["technologies_completed"] == 3 and _moved["wage_index"] == 0.0, _moved)

# --- the typed front end reaches all three, the same way it reaches everything else a player can type.
check("'capacity' types straight through", _PT2("capacity") == ({"cmd": "capacity"}, None), _PT2("capacity"))
check("'industry' and 'dashboard' are the same command by another name",
      _PT2("industry")[0] == {"cmd": "capacity"} and _PT2("dashboard")[0] == {"cmd": "capacity"},
      (_PT2("industry"), _PT2("dashboard")))
check("'changes 10' carries the number through", _PT2("changes 10") == ({"cmd": "changes", "years": 10.0}, None), _PT2("changes 10"))
check("bare 'changes' defaults to 5 years, not an error", _PT2("changes") == ({"cmd": "changes", "years": 5}, None), _PT2("changes"))
check("'economy full' carries the flag through", _PT2("economy full") == ({"cmd": "economy", "full": True}, None), _PT2("economy full"))
