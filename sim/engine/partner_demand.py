"""What a partner economy's own society makes and wants, at its own opening technologies (data, frozen for the game).

The foreign-trade module reads these through the bridge (`partner_own_economy`, `partner_household_demand`). Demand is its own
households' purchases of final goods (its population and income at its own solved prices, the household model the home market
uses for its ratios), held to the income they have; goods bought only as inputs to other goods are not traded until an
industrial demand model prices them."""
import functools

from .data import ROOT, calculated_goods_prices, goods_provenance, load_civ, starting_schedule
from .market_demand import MEAN_INCOME_HOURS_PER_CAPITA, household_demand_by_material
from .material_units import tonnes_per_unit


@functools.lru_cache(maxsize=None)
def foreign_solved_materials(civilization_id):
    """Materials the economy can make with its own technologies; the rest are priced only as if some technology were held."""
    civilization = load_civ(civilization_id)
    provenance = goods_provenance(frozenset(civilization["starting_techs"]), civilization_id=civilization_id)
    return frozenset(material for material, source in provenance.items() if source == "solved")


@functools.lru_cache(maxsize=None)
def foreign_prices_in_own_coin(civilization_id):
    """{material: price in the economy's own coin} under its own opening technologies (frozen for the game)."""
    civilization = load_civ(civilization_id)
    return calculated_goods_prices(
        frozenset(civilization["starting_techs"]), civilization_id=civilization_id,
        money_per_labour_hour=starting_schedule(civilization_id).money_per_labour_hour)


@functools.lru_cache(maxsize=None)
def _final_goods():
    """Goods a household buys for itself (named in data/world/needs.json)."""
    from . import need_data
    return frozenset(need_data.load_needs(ROOT)["goods"])


def budget_scaled_final_tonnes(prices_in_hours, population):
    """{material: tonnes a year} households buy for themselves at these
    prices (labour-hours per unit), scaled down uniformly when the model's
    spending exceeds the income they have. Goods bought as inputs to other
    goods are left out: the model's levels for those are not credible."""
    units = household_demand_by_material(prices_in_hours, population, MEAN_INCOME_HOURS_PER_CAPITA)
    spending = sum(quantity * prices_in_hours.get(material, 0.0)
                   for material, quantity in units.items())
    income = population * MEAN_INCOME_HOURS_PER_CAPITA
    scale = min(1.0, income / spending) if spending > 0.0 else 1.0
    final = _final_goods()
    return {material: quantity * scale * tonnes_per_unit(material)
            for material, quantity in units.items() if material in final}


@functools.lru_cache(maxsize=None)
def household_tonnes_by_material(civilization_id):
    """The economy's households' final-goods demand at its own solved prices."""
    civilization = load_civ(civilization_id)
    per_hour = starting_schedule(civilization_id).money_per_labour_hour
    prices_in_hours = {material: price / per_hour
                       for material, price in foreign_prices_in_own_coin(civilization_id).items()
                       if price > 0.0}
    return budget_scaled_final_tonnes(prices_in_hours, float(civilization.get("population") or 0.0))
