"""The opening's cost of a crop at the yield of the tiles that supply it.

The cost table prices a crop's run at the reference field (yield factor one). A tile makes the run's output times its
own yield factor, so a crop whose tiles yield little costs more per kilogram than the table says, and so does every
good made from it. The cost table is solved again with each arable recipe's outputs scaled to the yield of the tiles
that supply it (`crop_sites.supply_yield`: those at which a run pays at the price that yield implies), so the price a
household pays for a staple covers its cost on the tiles that grow it, and the producers placed there pay their way.
"""
import dataclasses
from typing import Dict, Mapping

from sim.economy.api import crop_sites, recipes_from_production_data, unit_cost

from . import port_costs

ARABLE_SOURCE = "arable land"   # the production entries' `extracted_from` for crops (some add a note after it)


def supply_yields(recipes, first_prices: Mapping[str, float], wages: Mapping[str, float],
                  fertility_by_tile: Mapping[str, float], people_by_tile: Mapping[str, float]) -> Dict[str, float]:
    """{arable recipe: yield factor its goods are made at}, from the cost table solved at the reference field
    (`first_prices`): a run's variable cost against its revenue there is the share of its cost that must be covered."""
    supplied: Dict[str, float] = {}
    for recipe_id, recipe in sorted(recipes.items()):
        revenue = unit_cost.revenue_per_run(recipe, first_prices)
        variable = unit_cost.variable_cost_per_run(recipe, first_prices, wages)
        if not (revenue > 0.0 and 0.0 < variable < float("inf")):
            continue
        factor = crop_sites.supply_yield(people_by_tile, fertility_by_tile, variable / revenue)
        if factor is not None and factor < 1.0:
            supplied[recipe_id] = factor
    return supplied


def with_outputs_at(production: Mapping[str, dict], yields: Mapping[str, float]) -> Dict[str, dict]:
    """The production entries with each recipe in `yields` making that factor of its stated outputs."""
    return {entry_id: (dict(entry, outputs={good: quantity * yields[entry_id] for good, quantity in entry["outputs"].items()})
                       if entry_id in yields else entry)
            for entry_id, entry in production.items()}


def opening_costs_at_tiles(sim, production_data, allowed, fertility_by_tile: Mapping[str, float],
                           people_by_tile: Mapping[str, float]) -> Dict[str, float]:
    """The cost table with the arable recipes `allowed` made at the yield of the tiles that supply them."""
    first = port_costs.opening_costs(sim)
    arable = [entry_id for entry_id in allowed
              if str(production_data[entry_id].get("extracted_from") or "").startswith(ARABLE_SOURCE)]
    recipes = recipes_from_production_data(production_data, arable)
    wage_of = port_costs.wage_function(sim, port_costs.cost_entries())
    wages = {trade: wage_of(trade) for recipe in recipes.values() for trade in recipe.labour_hours}
    yields = supply_yields(recipes, first, wages, fertility_by_tile, people_by_tile)
    if not yields:
        return first
    return port_costs.opening_costs(sim, with_outputs_at(port_costs.cost_entries(), yields))
