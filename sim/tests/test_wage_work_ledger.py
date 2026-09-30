"""Wage work shows in `money` and `log`; the shortage remedy tells the truth
about the player's own workings (complaints 148 and 175)."""
from .harness import *  # noqa: F401,F403

# --- complaint 148: one-off wage work -------------------------------------
_replies, _, _ = proto([
    {"cmd": "work", "trade": "scholar", "hours": 1500, "preview": True},
    {"cmd": "money"},
    {"cmd": "work", "trade": "scholar", "hours": 1500},
    {"cmd": "money"},
    {"cmd": "log"},
])
_preview, _money_before_work, _work, _money, _log = _replies[-5:]
check("`work ... preview` changes nothing and states the net",
      _preview.get("preview") and _preview.get("nothing_changed")
      and "so_you_are_up" in _preview
      and not _money_before_work.get("wage_work_this_year"),
      _preview)
check("the preview matches what the real work then reports",
      _preview.get("earned") == _work.get("earned")
      and _preview.get("it_cost_your_own_practice") == _work.get("it_cost_your_own_practice"),
      (_preview, _work))
_wage = _money.get("wage_work_this_year") or {}
check("`money` itemises wage income and the practice income it displaces",
      _wage.get("hours") == 1500 and _wage.get("wage_income") == _work["earned"]
      and _wage.get("practice_income_displaced", 0) > 0
      and abs(_wage["net"] - (_wage["wage_income"] - _wage["practice_income_displaced"])) < 0.2,
      _wage)
check("`work` says the lost practice income is simply not collected at the next step",
      "lands_at_next_step" in _work, _work)
check("`log` has a line for the wage work",
      "wage work" in str(_log).lower(), str(_log)[:400])

# --- complaint 148: the standing order, and the text screen -----------------
_replies, _, _ = proto([
    {"cmd": "allocate", "id": "work", "trade": "scholar", "hours": 1000},
    {"cmd": "step", "n": 1},
    {"cmd": "money"},
])
_standing_money = _replies[-1]
_wage = _standing_money.get("wage_work_last_year") or {}
check("a standing `allocate work` order also appears in `money` after the step",
      _wage.get("hours", 0) > 0 and _wage.get("wage_income", 0) > 0, _wage)

from sim.engine.proto.render_screens_economy import render_money
_text = render_money(_standing_money)
check("the money text shows the wage rows and no longer claims the rows "
      "add up to revenue while omitting wages",
      "wage work last year" in _text and "(these add up to the revenue above)" not in _text,
      _text)

# --- complaint 175: shortage remedy ----------------------------------------
_s = sim()

_s.annual_material_demand = lambda: {"gold_kg": 0.0}
_none = _s.shortage_remedy("gold")
check("no workings and no shortfall: the remedy says to sink one, not that "
      "your workings cover demand",
      "already cover" not in _none and "sink" in _none.lower(), _none)
_s.household.mines.append({"material": "gold", "capacity": 5.0})
_covered = _s.shortage_remedy("gold")
check("workings that do cover demand still say so",
      "already cover" in _covered, _covered)
