"""SCENARIO: a game's automatic mining, mine purchase and mines screen (Complaints 63 to 66, and the zero-cost guard
from 56). The order sizing and the shared capacity row rules are in `test_mine_auto_and_capacity`.

65: auto-mine counts a shaft still being sunk before ordering another.
66: a mine's commissioning year names the year that resolves it, and the
    capacity is visible the query after.
67: the capacity row for a material fed by two supply tags shows both demands.

Complaints 63, 64, 65 and the zero-cost mine guard.
"""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.economy import _agent_mines
from sim.ui.proto.dispatch_money import _cmd_buy


def _auto_mine_sim(pending_tonnes):
    test_sim = unopened_sim(capital=5_000_000_000_000.0, manual=False)
    test_sim.state.founder.policy["auto_mine"] = True
    test_sim.annual_material_demand = lambda: {"coal_kg": 1_000_000.0}
    test_sim.resource_throttle = lambda: 0.3
    test_sim.state.holdings.binding = "coal"
    test_sim.state.holdings.mine_pending["coal"] = pending_tonnes
    orders = []
    test_sim.open_mine = lambda material, tonnes, partial=True, order="": orders.append(tonnes) or 0.0
    test_sim._step_materials()
    return orders


# 65: pending tonnage covering the shortfall stops a second order.
_covered_orders = _auto_mine_sim(5_000_000.0)
check("auto-mine orders nothing when pending capacity covers the shortfall",
      not any(tonnes > 0 for tonnes in _covered_orders), _covered_orders)


# 66: the reported year is the year whose resolution commissions the mine.
_lead_sim = unopened_sim(capital=5_000_000.0)
_reply = _cmd_buy(_lead_sim, NODES, {"what": "mine", "material": "coal", "n": 10}, None)
_commission_year = _reply.get("commissions_during_year")
check("mine purchase names the year that commissions it",
      _commission_year is not None and "ready_year" in _reply, _reply)
if _commission_year is not None:
    _lead_sim.state.scenario.year = _commission_year - 1
    _lead_sim.commission_mines()
    check("resolving the year before commissions nothing",
          _lead_sim.mine_capacity.get("coal", 0.0) == 0.0)
    _lead_sim.state.scenario.year = _commission_year
    _lead_sim.commission_mines()
    check("resolving the named year commissions the capacity",
          _lead_sim.mine_capacity.get("coal", 0.0) > 0.0)
_screen_sim = unopened_sim(capital=5_000_000.0)
_screen_sim.open_mine("coal", 10.0)
_mines_screen = _agent_mines(_screen_sim)
check("the mines screen reports commissioning, not readiness",
      "ready_in" not in str(_mines_screen)
      and _mines_screen["mines_you_own"][0].get("commissions_during_year"),
      _mines_screen)

# 56 guard: a shaft that costs nothing to sink.
_free_sim = unopened_sim(capital=1000.0)
_free_sim._mine_capex_opex = lambda mat: (0.0, 1.0)
_free_sim.state.household.capital = -1_000_000.0
try:
    _free_sunk = _free_sim.open_mine("coal", 5.0, partial=False)
    _free_sim.mine_quote("coal", 5.0)
    _free_error = None
except ZeroDivisionError as error:
    _free_sunk, _free_error = 0.0, error
check("a zero-capex mine does not divide by zero", _free_error is None, _free_error)
check("a zero-capex mine is sunk even with no cash", _free_sunk == 5.0, _free_sunk)
check("a zero-capex mine costs nothing",
      _free_sim.state.household.capital == -1_000_000.0,
      _free_sim.state.household.capital)
