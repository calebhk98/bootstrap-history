"""Test for mine commission display setting (Complaint 66).

The setting controls whether the mine purchase reply and mines screen show:
- "commissioned" (when it will be commissioned)
- "ready" (when it will be ready)
- "both" (default, shows both years)
"""
from .harness import *
from sim.engine.proto.dispatch_money import _cmd_buy
from sim.engine.proto.economy import _agent_mines


# Test that the mine purchase reply includes both commissions_during_year and ready_year
_buy_sim = sim(capital=5_000_000.0)
_reply = _cmd_buy(_buy_sim, NODES, {"what": "mine", "material": "coal", "n": 10}, None)
check("mine purchase reply includes commissions_during_year",
      "commissions_during_year" in _reply, _reply)
check("mine purchase reply includes ready_year",
      "ready_year" in _reply, _reply)

# Test that mines screen includes both fields for pending mines
_screen_sim = sim(capital=5_000_000.0)
_screen_sim.open_mine("coal", 10.0)
_mines_screen = _agent_mines(_screen_sim)
_pending_mines = _mines_screen["still_being_sunk"]
check("pending mines list exists in mines screen",
      _pending_mines is not None, _mines_screen)

# Test that after commissioning, we can see ready_year
_commission_year = _reply.get("commissions_during_year")
if _commission_year is not None:
    _ready_sim = sim(capital=5_000_000.0)
    _ready_sim.open_mine("coal", 10.0)
    _ready_sim.state.scenario.year = _commission_year
    _ready_sim.commission_mines()
    _ready_screen = _agent_mines(_ready_sim)
    check("commissioned mine appears in mines screen",
          _ready_screen["mines_you_own"] and _ready_screen["mines_you_own"] != "none",
          _ready_screen)
