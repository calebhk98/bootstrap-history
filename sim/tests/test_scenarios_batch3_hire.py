"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenario: the `hire` command reports a short hire, and `ventures` carries the craft
lists the supervision check counts. The rules are plain functions with tests of their own:
test_complaint_583_partial_hire_and_craft_help."""
from unittest import mock

from .harness import *  # noqa: F401,F403
from sim.labour.labour_market_api import LabourMarket

ASKED, FOUND = 4, 1
_game = unopened_sim(capital=5_000_000.0)
with mock.patch.object(LabourMarket, "whole_recruits", return_value=FOUND):
    _short = S._agent_dispatch(_game, NODES, {"cmd": "hire", "trade": "artisan", "n": ASKED})
check("scenario hire: a short hire is ok, says how many were found of how many asked, and why",
      _short.get("ok") is True and _short.get("hired") == FOUND and _short.get("asked") == ASKED
      and _short.get("cause") == "search_found_fewer" and _short.get("trade") == "artisan", _short)
_full = S._agent_dispatch(unopened_sim(capital=5_000_000.0), NODES, {"cmd": "hire", "trade": "artisan", "n": 1})
check("scenario hire: a full hire carries no shortfall cause", _full.get("ok") and "cause" not in _full, _full)
_note = _game.labour.craft_trades_report()
_screen = S._agent_dispatch(_game, NODES, {"cmd": "ventures"})
check("scenario hire: the ventures reply carries the lists the supervision check counts",
      _screen.get("these_are_not_interchangeable_trades") == _note
      and all(_game.labour.is_craft_trade(trade) for trade in _note["craft"])
      and not any(_game.labour.is_craft_trade(trade) for trade in _note["not_craft"]), _screen.get("these_are_not_interchangeable_trades"))
