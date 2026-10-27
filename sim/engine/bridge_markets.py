"""Bridge entries the markets module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine as the old mixin code did,
and is never cached. `household_demand_units` is the household need model (market_demand.py), which the partner economies'
demand calls as well; `household_basket` is the need basket the actors' budgets read."""
from sim.agents.api import relations
from sim.assembly.api import KEYED, QUOTE
from sim.markets.api import RepriceOpeningMoney

from . import market_demand, need_substitutes, opening_money
from .bridge import bridge_command, bridge_view
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


# ---- workforce: facts of the labour package no workforce view answers yet ----

@bridge_view("settlement_tiles")
def settlement_tiles(sim):
    """{tile id: people living there} for the tiles the nation holds."""
    return sim.labour.settlement_tiles()


@bridge_view("labour_need_shares")
def labour_need_shares(sim):
    """{trade: share of the hours the society's needs ask of it}."""
    return sim.labour.need_shares()


# ---- the need data and the relations store ----

@bridge_view("material_serves_a_need", kind=KEYED)
def material_serves_a_need(sim, material):
    """Whether the needs data names the material as serving some household need."""
    return need_substitutes.serves_a_need(material)


@bridge_view("border_terms", kind=QUOTE)
def border_terms(sim, destination, source):
    """(tariff share, embargoed) that the state of `destination` holds toward goods crossing from `source`, read from the
    relations store."""
    return relations.tariff_on(sim.stores, destination, source), relations.embargoes(sim.stores, destination, source)


# ---- commands: the opening's money ----

@bridge_command(RepriceOpeningMoney)
def reprice_opening_money(sim, command):
    """Every seat's purse and the tree's money fields move to the money an hour of work is worth at the economy."""
    opening_money.reprice_opening_money(sim, command.before)
