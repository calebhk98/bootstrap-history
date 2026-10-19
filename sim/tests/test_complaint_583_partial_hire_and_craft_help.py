"""Complaints/583: a partial hire says how many were hired and why; the craft help reads the supervision trade data."""
from unittest import mock

from .harness import *  # noqa: F401,F403

from sim.labour.labour_market_api import LabourMarket
from sim.engine.data import TRADE_FAMILY

ASKED, FOUND = 4, 1
game = sim(capital=5_000_000.0)
with mock.patch.object(LabourMarket, "whole_recruits", return_value=FOUND):
    reply = S._agent_dispatch(game, NODES, {"cmd": "hire", "trade": "artisan", "n": ASKED})
check("a short hire is still ok", reply.get("ok") is True, reply)
check("hired is the number found", reply.get("hired") == FOUND, reply)
check("asked is the number requested", reply.get("asked") == ASKED, reply)
check("the shortfall carries a cause", reply.get("cause") == "search_found_fewer", reply)
check("the trade is named in its own field", reply.get("trade") == "artisan", reply)

full = S._agent_dispatch(sim(capital=5_000_000.0), NODES, {"cmd": "hire", "trade": "artisan", "n": 1})
check("a full hire carries no shortfall cause", full.get("ok") and "cause" not in full, full)

# the help's craft and non-craft trades are the ones the supervision check counts
note = game.labour.craft_trades_report()
check("help names the craft trades the supervision check counts",
      sorted(note["craft"]) == sorted(t for t, f in TRADE_FAMILY.items() if f == "craft")
      and all(game.labour.is_craft_trade(t) for t in note["craft"]), note)
check("help names the trades that do not supervise as craft",
      "labourer" in note["not_craft"] and not any(game.labour.is_craft_trade(t) for t in note["not_craft"]), note)
screen = S._agent_dispatch(game, NODES, {"cmd": "ventures"})
shown = screen.get("these_are_not_interchangeable_trades")
check("the ventures reply carries the same lists", shown == note, shown)
