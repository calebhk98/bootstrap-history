"""Migration: workers re-weigh their area against the routes out of it, trade by trade.

A worker's skills are portable, so a worker of one trade considers the same trade at the end of each
route. The score of a destination is the log of its real expected income (income over that area's
subsistence) less the origin's, less the moving cost counted in years of the origin's subsistence.
Staying scores zero. Flows are all computed from the counts at the start of the step and applied after,
so the order of areas does not matter. Trainees stay where they train.
"""
import math
from typing import Dict, List, Tuple

from sim.constants import declare

from .expectations import expected_income, index_clearings, logit_shares
from .records import Clearing, MarketState, Route, YearInputs, YearReport

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

STAY = "stay"


def _real_income(state, inputs, clearings, area: str, trade: str, cache: Dict[Tuple[str, str], float]) -> float:
    """Expected income over the area's subsistence; zero when the area has no subsistence figure."""
    key = (area, trade)
    if key not in cache:
        floor = inputs.subsistence_per_worker_year.get(area, 0.0)
        cache[key] = expected_income(state, inputs, clearings, area, trade) / floor if floor > 0.0 else 0.0
    return cache[key]


def _sorted_routes(routes: List[Route]) -> List[Route]:
    return sorted(routes, key=lambda route: (route.destination, route.moving_cost))


def migrate(state: MarketState, inputs: YearInputs, clearings: Dict[Tuple[str, str], Clearing],
            report: YearReport) -> None:
    """Move workers along the routes; record the net change per area in `report.migrated`."""
    index = clearings if isinstance(clearings, dict) else index_clearings(clearings)
    cache: Dict[Tuple[str, str], float] = {}
    flows: List[Tuple[str, str, str, List[float]]] = []   # (origin, destination, trade, people per band)

    for origin in sorted(inputs.routes):
        floor = inputs.subsistence_per_worker_year.get(origin, 0.0)
        routes = _sorted_routes(inputs.routes[origin])
        if floor <= 0.0 or not routes:
            continue
        for trade in sorted(state.workers.get(origin, {})):
            bands = state.workers[origin][trade]
            if sum(bands) <= 0.0:
                continue
            real_origin = _real_income(state, inputs, index, origin, trade, cache)
            if real_origin <= 0.0:
                continue
            scores: Dict[str, float] = {STAY: 0.0}
            for position, route in enumerate(routes):
                if route.destination == origin:
                    continue
                real_destination = _real_income(state, inputs, index, route.destination, trade, cache)
                if real_destination <= 0.0:
                    continue
                cost_in_years = route.moving_cost / floor
                scores[str(position)] = (math.log(real_destination) - math.log(real_origin)
                                         - MIGRATION_COST_WEIGHT * cost_in_years)
            if len(scores) == 1:
                continue
            shares = logit_shares(scores, MIGRATION_TASTE_SCALE)
            for position, route in enumerate(routes):
                share = shares.get(str(position), 0.0) * MIGRATION_CONSIDERATION_SHARE_PER_YEAR
                if share > 0.0:
                    flows.append((origin, route.destination, trade, [count * share for count in bands]))

    for origin, destination, trade, moved in flows:
        origin_bands = state.workers[origin][trade]
        destination_bands = state.workers.setdefault(destination, {}).setdefault(trade, [0.0] * len(origin_bands))
        for band, amount in enumerate(moved):
            origin_bands[band] -= amount
            destination_bands[band] += amount
        total = sum(moved)
        report.migrated[origin] = report.migrated.get(origin, 0.0) - total
        report.migrated[destination] = report.migrated.get(destination, 0.0) + total
