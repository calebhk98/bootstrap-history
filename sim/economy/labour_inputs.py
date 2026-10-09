"""What the economy hands the labour core each year besides the bids: the outside option, people coming
of working age and leaving work, and the routes between tiles.

Entrants and attrition are shares of working people the engine takes from demography (`YearInputs`).
A route runs to each bordering tile; moving a person costs carrying him and his belongings the cheapest
way between the tiles.
"""
import math
from typing import Dict, List

from sim.constants import declare
from sim.labour.api import CAREER_YEARS, Route, YearInputs as CoreInputs, people_in

from .households_cohort import VALUE_OF_LIFE_YEARS_OF_INCOME
from .households_orders import HOUSEHOLD_TIME_PREFERENCE
from .labour_ask_floor import ask_floor_by_tile
from .setup import labour_area
from .year_labour import outside_option_by_tile

TONNES_CARRIED_PER_MIGRANT = declare(
    "TONNES_CARRIED_PER_MIGRANT", 0.1, kind="temporary_heuristic", unit="tonnes",
    source=None, confidence="D",
    why="A person and what he takes when he moves, priced at the freight rate between tiles. His own "
        "mass is about a tenth of a tonne; what he brings, the time lost on the road and the risk "
        "of it are not modelled.")


def routes_by_area(setup, carriage) -> Dict[str, List[Route]]:
    """Each tile's way out to each tile it borders, at the cost of carrying a migrant there."""
    routes: Dict[str, List[Route]] = {}
    for tile_id, tile in sorted(setup.tiles.items()):
        for neighbour in sorted(tile.borders):
            cost = carriage.cost_per_tonne(tile_id, neighbour) if neighbour in setup.tiles else math.inf
            if math.isfinite(cost):
                routes.setdefault(labour_area(tile_id), []).append(
                    Route(labour_area(neighbour), cost * TONNES_CARRIED_PER_MIGRANT))
    return routes


def labour_context(setup, record, view, carriage, inputs, own_plot_options=None) -> CoreInputs:
    """The core's inputs for the year without trades or bids (the clearing adds them). `own_plot_options`
    (households_own.own_production_options) sets how low a worker's ask can fall: to what the plot gives."""
    outside = outside_option_by_tile(setup, record, view)
    plot = ask_floor_by_tile(setup, record, view, own_plot_options or {})
    areas = [labour_area(tile) for tile in sorted(setup.tiles)]
    return CoreInputs(
        trades={}, bids=(),
        subsistence_per_worker_year={labour_area(tile): cost for tile, cost in outside.items()},
        ask_floor_per_worker_year={labour_area(tile): value for tile, value in plot.items()},
        hours_per_worker_year=setup.working_hours_per_year,
        discount_rate=HOUSEHOLD_TIME_PREFERENCE, career_years=CAREER_YEARS,
        entrants={area: people_in(record.workforce, area) * inputs.entrant_share for area in areas},
        attrition_share={area: inputs.attrition_share for area in areas},
        routes=routes_by_area(setup, carriage),
        value_of_life_years_of_income=VALUE_OF_LIFE_YEARS_OF_INCOME)
