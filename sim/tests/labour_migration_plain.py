"""The plain Python rule of migration as it ran before the tables kernels (`migration_kernel`): kept so a test runs both on the
same inputs. Not used by the game."""
import math
from typing import Dict, List, Optional, Tuple

from sim.labour.market.expectations import expected_income, index_clearings
from sim.labour.market.migration import move_shares
from sim.labour.market.records import LabourClearing, MarketState, Route, YearInputs, YearReport


def _real_income(state, inputs, clearings, area: str, trade: str, cache: Dict[Tuple[str, str], Optional[float]]) -> Optional[float]:
    """Expected income after the state's take, over the area's subsistence; None when the area has no subsistence figure."""
    key = (area, trade)
    if key not in cache:
        floor = inputs.subsistence_per_worker_year.get(area)
        kept = 1.0 - min(1.0, max(0.0, inputs.taxed_share.get(area, 0.0)))
        cache[key] = kept * expected_income(state, inputs, clearings, area, trade) / floor if floor else None
    return cache[key]


def _sorted_routes(routes: List[Route]) -> List[Route]:
    return sorted(routes, key=lambda route: (route.destination, route.moving_cost))


def migrate(state: MarketState, inputs: YearInputs, clearings: Dict[Tuple[str, str], LabourClearing],
            report: YearReport) -> None:
    """Move workers along the routes; record the net change per area in `report.migrated`."""
    index = clearings if isinstance(clearings, dict) else index_clearings(clearings)
    cache: Dict[Tuple[str, str], Optional[float]] = {}
    flows: List[Tuple[str, str, str, List[float]]] = []   # (origin, destination, trade, people per band)

    for origin in sorted(inputs.routes):
        floor = inputs.subsistence_per_worker_year.get(origin)
        routes = _sorted_routes(inputs.routes[origin])
        if not floor or floor <= 0.0 or not routes:
            continue
        for trade in sorted(state.workers.get(origin, {})):
            bands = state.workers[origin][trade]
            if sum(bands) <= 0.0:
                continue
            real_origin = _real_income(state, inputs, index, origin, trade, cache)
            if real_origin is None or real_origin <= 0.0:
                continue
            options = [(None, 0.0) if route.destination == origin else
                       (_real_income(state, inputs, index, route.destination, trade, cache),
                        (route.moving_cost + route.expected_penalty) / floor) for route in routes]
            for position, share in enumerate(move_shares(real_origin, options)):
                if share > 0.0:
                    flows.append((origin, routes[position].destination, trade, [count * share for count in bands]))

    for origin, destination, trade, moved in flows:
        origin_bands = state.workers[origin][trade]
        destination_bands = state.workers.setdefault(destination, {}).setdefault(trade, [0.0] * len(origin_bands))
        for band, amount in enumerate(moved):
            origin_bands[band] -= amount
            destination_bands[band] += amount
        total = sum(moved)
        report.migrated[origin] = report.migrated.get(origin, 0.0) - total
        report.migrated[destination] = report.migrated.get(destination, 0.0) + total
