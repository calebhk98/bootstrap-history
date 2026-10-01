"""Complaint 163: the household-room advice (`labour`, the `hire` refusal)
must name `buy housing N` first, priced by the same function `quote housing`
uses, and only then the tech nodes."""
from .harness import *  # noqa: F401,F403

_room_sim = sim(capital=1000000.0)
_advice = _room_sim._room_advice()
_ok_hire, _refusal = _room_sim.hire("smith", 20)
_unit_price = _room_sim.HOUSING_COST_PER_PLACE * _room_sim.price_index

check("room advice offers 'buy housing' before any tech node",
      "buy housing" in _advice and _advice.index("buy housing") < _advice.index("workshop_first"),
      _advice)
check("...with the per-place price `quote housing` charges",
      ("%.0f" % _unit_price) in _advice.replace(",", ""), (_unit_price, _advice))
check("the hire refusal also names 'buy housing' before the nodes",
      not _ok_hire and "buy housing" in _refusal
      and _refusal.index("buy housing") < _refusal.index("workshop_first"), _refusal)
check("the hire refusal no longer claims room is not bought",
      "Room is not bought" not in _refusal, _refusal)
