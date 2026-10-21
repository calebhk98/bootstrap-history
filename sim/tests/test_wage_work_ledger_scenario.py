"""Scenarios (complaint 144 and 640): wage work of a played game shows in `money` and `log`, once as one-off work and once as
a standing order. The remedy and the money text are in test_wage_work_ledger."""
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
check("`work ... preview` changes nothing and states the wage",
      _preview.get("preview") and _preview.get("nothing_changed")
      and _preview.get("earned", 0) > 0
      and not _money_before_work.get("wage_work_this_year"),
      _preview)
check("the preview matches what the real work then reports",
      _preview.get("earned") == _work.get("earned"),
      (_preview, _work))
_wage = _money.get("wage_work_this_year") or {}
check("`money` itemises the hours sold and the wage income, and no displaced practice",
      _wage.get("hours") == 1500 and _wage.get("wage_income") == _work["earned"]
      and "practice_income_displaced" not in _wage and "net" not in _wage,
      _wage)
check("`log` has a line for the wage work",
      any(entry.get("event_kind") == "wage_work_sold" for entry in _log.get("entries", [])), str(_log)[:400])

# --- complaint 144: the standing order, and the text screen -----------------
_game = sim()
_game.end_year = _game.cfg["start_year"] + _game.cfg["horizon_years"]
_ask(cmd="allocate", id="work", trade="scholar", hours=1000)
_ask(cmd="step", years=1)
_standing_money = _ask(cmd="money")
_wage = _standing_money.get("wage_work_last_year") or {}
check("a standing `allocate work` order also appears in `money` after the step",
      _wage.get("hours", 0) > 0 and _wage.get("wage_income", 0) > 0, _wage)
