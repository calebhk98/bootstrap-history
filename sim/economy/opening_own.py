"""What households grow for themselves at the opening, so the opening sizes producers for what is left to buy.

In every simulated year the hours nobody hires go into the household's own plot (households_own.py). The
opening estimates the same split before any producer is placed: the hours the demand needs are hired, the
rest of what the cohort offers is idle and grows its floors, and the floor bids are cut by what was grown.
"""
import math
from typing import Dict, Mapping

from sim.constants import declare

from . import opening_income
from .households_own import own_production
from .types import GoodId, TileId

HIRING_FOLLOWS_DEMAND_SHARE = declare(
    "HIRING_FOLLOWS_DEMAND_SHARE", 1.0, kind="temporary_heuristic",
    unit="share of the opening's hired hours placed on tiles by their share of final demand value", source=None,
    confidence="D", retire="Complaints/545: placing producers before settling income",
    why="Producers are placed after income is settled, so where the opening's hired hours fall is not yet known; "
        "they are spread by where the final demand is, the rest by working people.")


def hired_hours_by_cohort(setup, cohorts: Mapping[str, object], final_by_tile: Mapping[TileId, Mapping[GoodId, float]],
                          runs: Mapping[str, float], prices: Mapping[GoodId, float]) -> Dict[str, float]:
    """Hours the runs the demand needs hire from each cohort: the total spread over tiles by their share of final
    demand value (and working people), within a tile over cohorts by working people."""
    total = math.fsum(count * math.fsum(setup.recipes[recipe_id].labour_hours.values())
                      for recipe_id, count in runs.items())
    demand_value = {tile: opening_income.value_of({tile: demand}, prices) for tile, demand in final_by_tile.items()}
    working: Dict[TileId, float] = {}
    for cohort in cohorts.values():
        working[cohort.tile] = working.get(cohort.tile, 0.0) + cohort.working_people
    value_total = math.fsum(demand_value.values())
    working_total = math.fsum(working.values())
    hired: Dict[str, float] = {}
    for agent_id, cohort in cohorts.items():
        tile_working = working[cohort.tile]
        by_demand = demand_value.get(cohort.tile, 0.0) / value_total if value_total > 0.0 else 0.0
        by_people = tile_working / working_total if working_total > 0.0 else 0.0
        tile_share = HIRING_FOLLOWS_DEMAND_SHARE * by_demand + (1.0 - HIRING_FOLLOWS_DEMAND_SHARE) * by_people
        hired[agent_id] = total * tile_share * (cohort.working_people / tile_working if tile_working > 0.0 else 0.0)
    return hired


def grown_units_by_cohort(setup, cohorts: Mapping[str, object], final_by_tile, runs: Mapping[str, float],
                          prices: Mapping[GoodId, float], options) -> Dict[str, Dict[str, float]]:
    """Need units each cohort grows from the hours it offers less the hours hired (as the year's first pass does)."""
    if not options:
        return {}
    hired = hired_hours_by_cohort(setup, cohorts, final_by_tile, runs, prices)
    grown: Dict[str, Dict[str, float]] = {}
    for agent_id, cohort in sorted(cohorts.items()):
        tile = setup.tiles.get(cohort.tile)
        idle = cohort.working_people * setup.working_hours_per_year - hired[agent_id]
        _moves, _goods, units = own_production(cohort, idle, options, setup.recipes, tile.fertility if tile else 0.0,
                                               setup.basket_for(cohort.tile))
        if units:
            grown[agent_id] = units
    return grown
