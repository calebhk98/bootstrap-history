"""Scenario for Complaint 64 in a whole game: buying a mine answers with the year it is commissioned and the year it is
ready, the mines screen lists it while it is being sunk, and once commissioned it is a mine you own. The display setting
is in test_commission_display_setting."""
from .harness import *
from sim.ui.proto.dispatch_money import _cmd_buy
from sim.ui.proto.economy import _agent_mines

_buy_sim = sim(capital=5_000_000.0)
_reply = _cmd_buy(_buy_sim, NODES, {"what": "mine", "material": "coal", "n": 10}, None)

_screen_sim = sim(capital=5_000_000.0)
_screen_sim.open_mine("coal", 10.0)
_pending = _agent_mines(_screen_sim)["still_being_sunk"]

_commission_year = _reply.get("commissions_during_year")
_ready_sim = sim(capital=5_000_000.0)
_ready_sim.open_mine("coal", 10.0)
_ready_sim.state.scenario.year = _commission_year
_ready_sim.commission_mines()
_owned = _agent_mines(_ready_sim)["mines_you_own"]

check("scenario: a mine purchase names its commission and ready years, is listed while sunk, and is owned once commissioned",
      "commissions_during_year" in _reply and "ready_year" in _reply and _commission_year is not None
      and bool(_pending) and bool(_owned) and _owned != "none",
      dict(reply=_reply, pending=_pending, owned=_owned))
