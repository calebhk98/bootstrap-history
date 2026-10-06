"""Wage work shows in `money` and `log`; the shortage remedy tells the truth
about the player's own workings (complaints 144 and 171)."""
from .harness import *  # noqa: F401,F403

# --- complaint 144: one-off wage work -------------------------------------
_game = sim()


def _ask(**command):
    return S._agent_dispatch(_game, NODES, command)


_preview = _ask(cmd="work", trade="scholar", hours=1500, preview=True)
_money_before_work = _ask(cmd="money")
_work = _ask(cmd="work", trade="scholar", hours=1500)
_money = _ask(cmd="money")
_log = _ask(cmd="log")
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
check("`log` has a line for the wage work",
      "wage work" in str(_log).lower(), str(_log)[:400])

# --- complaint 144: the standing order, and the text screen -----------------
_game = sim()
_game.end_year = _game.cfg["start_year"] + _game.cfg["horizon_years"]
_ask(cmd="allocate", id="work", trade="scholar", hours=1000)
_ask(cmd="step", years=1)
_standing_money = _ask(cmd="money")
_wage = _standing_money.get("wage_work_last_year") or {}
check("a standing `allocate work` order also appears in `money` after the step",
      _wage.get("hours", 0) > 0 and _wage.get("wage_income", 0) > 0, _wage)

from sim.ui.proto.render_screens_economy import render_money
_text = render_money(_standing_money)
check("the money text shows the wage rows and no longer claims the rows "
      "add up to revenue while omitting wages",
      "wage work last year" in _text and "(these add up to the revenue above)" not in _text,
      _text)

# --- complaint 171: shortage remedy ----------------------------------------
_s = _game

_s.annual_material_demand = lambda: {"gold_kg": 0.0}
_none = _s.shortage_remedy("gold")
check("no workings and no shortfall: the remedy says to sink one, not that "
      "your workings cover demand",
      "already cover" not in _none and "sink" in _none.lower(), _none)
_s.household.mines.append({"material": "gold", "capacity": 5.0})
_covered = _s.shortage_remedy("gold")
check("workings that do cover demand still say so",
      "already cover" in _covered, _covered)
