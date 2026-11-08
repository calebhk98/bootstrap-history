"""Migration: workers re-weigh their area against the routes out of it, trade by trade.

A worker's skills are portable, so a worker of one trade considers the same trade at the end of each
route. The score of a destination is the log of its real expected income (income over that area's
subsistence) less the origin's, less the moving cost counted in years of the origin's subsistence.
Income is what a worker keeps after the state's take in that area (`YearInputs.taxed_share`: a heavier take at home,
a collective liability falling on the stayers, is a reason to go), and a route's cost includes what a leaver expects to
pay if recaptured (`Route.expected_penalty`). Staying scores zero. Flows are all computed from the counts at the start of the step and applied after,
so the order of areas does not matter. Trainees stay where they train. The net change per area is a request to the
owner of people (demography), which moves them once, with its own food-driven moves.
"""
import math
from typing import Dict, List, Optional, Tuple

import numpy as np

from sim.constants import declare

from . import migration_kernel
from .records import MarketState, Route, YearInputs, YearReport
from .results_grid import grid_of
from .year_rates import rates_of

MIGRATION_TASTE_SCALE = declare(
    "MIGRATION_TASTE_SCALE", 0.5, kind="temporary_heuristic", unit="log real income",
    source=None, confidence="D",
    why="Spread of the unobserved tastes (kin, language, land) in the choice between staying and each "
        "route; bigger is noisier and flatter. Not fitted.")

MIGRATION_COST_WEIGHT = declare(
    "MIGRATION_COST_WEIGHT", 1.0, kind="temporary_heuristic", unit="log real income per year of subsistence",
    source=None, confidence="D",
    why="How heavily a move's cost, counted in years of the origin's subsistence, weighs against the log "
        "gain in real income. One means a year of subsistence spent counts as a year of income lost.")

MIGRATION_CONSIDERATION_SHARE_PER_YEAR = declare(
    "MIGRATION_CONSIDERATION_SHARE_PER_YEAR", 0.05, kind="temporary_heuristic", unit="share of workers a year",
    source=None, confidence="D",
    why="Share of a trade's workers in an area who weigh moving in a given year; the rest do not look. "
        "Keeps even a large gain from emptying an area at once. Not fitted to any migration record.")



def move_shares(real_origin: float, options: List[Tuple[Optional[float], float]]) -> List[float]:
    """Share of the people of one place who move along each option this year. An option is the real income at its
    end (income over that place's subsistence; None or not above zero means it cannot be weighed) and the moving cost
    in years of the origin's subsistence. Staying is an option scoring zero; only the share who consider moving at all
    can go. The rule for workers between market areas and for people between regions alike (`migration_kernel.move_shares`
    is the same rule over arrays)."""
    log_origin = math.log(real_origin)
    scores = [None if real_destination is None or real_destination <= 0.0 else
              math.log(real_destination) - log_origin - MIGRATION_COST_WEIGHT * cost_in_years
              for real_destination, cost_in_years in options]
    weighed = [score for score in scores if score is not None]
    if not weighed:
        return [0.0] * len(options)
    top = max(0.0, max(weighed))      # the stay option scores zero
    stay_weight = math.exp((0.0 - top) / MIGRATION_TASTE_SCALE)
    weights = [0.0 if score is None else math.exp((score - top) / MIGRATION_TASTE_SCALE) for score in scores]
    total = math.fsum(weights) + stay_weight
    return [weight / total * MIGRATION_CONSIDERATION_SHARE_PER_YEAR for weight in weights]


def _routes(state: MarketState, inputs: YearInputs) -> migration_kernel.Routes:
    """The routes out of every area as arrays grouped by origin, each origin's sorted by (destination, moving cost)."""
    ids = state.ids
    areas = len(ids.areas)
    first, count = np.zeros(areas, np.int64), np.zeros(areas, np.int64)
    destination, cost, penalty = [], [], []
    for origin in sorted(inputs.routes):
        if ids.areas.find(origin) is None:
            continue
        ways = sorted(inputs.routes[origin], key=lambda route: (route.destination, route.moving_cost))
        first[ids.areas.number(origin)], count[ids.areas.number(origin)] = len(destination), len(ways)
        destination.extend(ids.areas.number(route.destination) for route in ways)
        cost.extend(route.moving_cost for route in ways)
        penalty.extend(route.expected_penalty for route in ways)
    taxed = np.zeros(areas)
    for area, share in inputs.taxed_share.items():
        if ids.areas.find(area) is not None:
            taxed[ids.areas.number(area)] = share
    return migration_kernel.Routes(first, count, np.array(destination, np.int64), np.array(cost), np.array(penalty), taxed)


def migrate(state: MarketState, inputs: YearInputs, clearings, report: YearReport) -> None:
    """Move workers along the routes; record the net change per area in `report.migrated`. Flows are all computed from the
    counts at the start of the step (`migration_kernel.find_flows`) and applied after (`apply_flows`)."""
    state.admit([name for name in inputs.routes] + [route.destination for ways in inputs.routes.values() for route in ways], list(inputs.trades))
    grid = grid_of(state, clearings.values() if isinstance(clearings, dict) else clearings)
    routes = _routes(state, inputs)
    if not len(routes.destination):
        return
    rates = rates_of(state, inputs)
    rules = migration_kernel.MigrationRules(MIGRATION_TASTE_SCALE, MIGRATION_COST_WEIGHT, MIGRATION_CONSIDERATION_SHARE_PER_YEAR)
    longest = max([int(grid.results.demand_count.max())] if len(grid.results.demand_count) else [1])
    scratch_caps, scratch_hours = np.empty(longest + 1), np.empty(longest + 1)
    capacity = len(routes.destination) * len(state.ids.trades)
    bands = state.bands
    flow_origin, flow_route, flow_trade = np.empty(capacity, np.int64), np.empty(capacity, np.int64), np.empty(capacity, np.int64)
    flow_people = np.empty((capacity, bands))
    found = migration_kernel.find_flows(rates, rules, grid.results, grid.demand_caps, grid.demand_hours, state.workers_table, routes,
                                        scratch_caps, scratch_hours, flow_origin, flow_route, flow_trade, flow_people)
    area_count = len(state.ids.areas)
    migrated, seen, order = np.zeros(area_count), np.zeros(area_count, np.bool_), np.zeros(area_count, np.int64)
    counter = np.array([state._order], np.int64)
    migration_kernel.apply_flows(state.workers_table, state.areas_table, counter, routes, len(state.ids.trades), flow_origin, flow_route, flow_trade,
                                 flow_people, found, migrated, seen, order)
    state._order = int(counter[0])
    for area in np.flatnonzero(seen)[np.argsort(order[seen], kind="stable")].tolist():
        report.migrated[state.ids.areas.names[area]] = float(migrated[area])
