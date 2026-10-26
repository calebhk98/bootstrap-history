"""Bridge entries the markets module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine as the old mixin code did,
and is never cached. `household_demand_units` is the household need model (market_demand.py), which the partner economies'
demand calls as well; `household_basket` is the need basket the actors' budgets read."""
from sim.assembly.api import QUOTE

from . import market_demand
from .bridge import bridge_view
from .data import calculated_goods_table


# ---- core: facts of the game the module cannot read from an owner yet ----

@bridge_view("opening_farmed_hectares")
def opening_farmed_hectares(sim):
    """The area the opening's farm cleared (an initial condition)."""
    return sim._opening_farmed_hectares


@bridge_view("household_demand_units", kind=QUOTE)
def household_demand_units(sim, prices_in_hours, population, income_per_capita):
    """{material: units a year} households (and what they buy through recipes) want at these labour-hour prices, with the
    warmth, clothing and shelter floors the civilisation's tiles' climate sets."""
    return market_demand.household_demand_by_material(prices_in_hours, population, income_per_capita, sim.civ, sim.world_map)


@bridge_view("household_basket")
def household_basket(sim):
    return market_demand.household_basket(sim.civ, sim.world_map)


# ---- prices ----

@bridge_view("calculated_goods_prices", kind=QUOTE)
def calculated_goods_prices(sim, held, farmed_hectares):
    """{material: labour-hour price} of every material the solver prices when `held` techniques are known and
    `farmed_hectares` are farmed (banded), from one solve."""
    from sim.prices.api import prices as price_solver
    in_hours, _basis = calculated_goods_table(
        held, civilization_id=sim.civ.get("id"), civilization=sim.civ,
        farmed_hectares=price_solver.band_farmed_hectares(farmed_hectares))
    return in_hours


# ---- production ----

@bridge_view("workshop_output")
def workshop_output(sim):
    """Money the seat's own workshop takes in a year, before the market ceiling."""
    return sim.workshop_output()


@bridge_view("concern_market")
def concern_market(sim):
    """{node id: yearly takings} of every concern the seat's ledger counts."""
    return sim.ledger_concern_rows()
