"""A trade with vacancies and no people in an area gets its first hands (Complaint 644).

Run after the year's switching and migration. For each (area, trade) where employers want hours and no
one of the trade works or trains, the first people come from the routes that need no teacher: migrants from
areas that hold the trade (up to their spare hands), then bonded people for sale where the area's
civilisation allows it (`trade_formation.first_people_plan` orders the same routes for any caller). Conversion
needs a teacher and a payer, so the caller's own verbs (training schools) carry it out. Any employer's
vacancy counts, not one actor's.
"""
from typing import Dict, List, Tuple

from . import aptitude
from .expectations import index_clearings
from .records import MarketState, YearInputs, YearReport


def spare_people(workers: float, hours_wanted: float, hours_per_worker_year: float) -> float:
    """People of a trade an area could release: its workers less those its employers' bids still need."""
    return max(0.0, workers - max(0.0, hours_wanted) / max(hours_per_worker_year, 1e-12))


def bonded_available(bondage_allowed: bool, bonded_for_sale: float) -> float:
    """Bonded people of a trade an actor may buy: those for sale where the civilisation recognises bondage,
    none where it does not."""
    return max(0.0, bonded_for_sale) if bondage_allowed else 0.0


def migration_takes(wanted: float, migrant_spare: Dict[str, float]) -> List[Tuple[str, float]]:
    """(origin area, people) drawn from the areas with most spare hands first, until `wanted` is met."""
    takes = []
    remaining = wanted
    for area in sorted(migrant_spare, key=lambda name: (-migrant_spare[name], name)):
        take = min(remaining, max(0.0, migrant_spare[area]))
        if take > 0.0:
            takes.append((area, take))
            remaining -= take
    return takes


def _held(state: MarketState, area: str, trade: str) -> float:
    held = sum(state.workers.get(area, {}).get(trade, ()))
    for cohort in state.trainees.get(area, {}).get(trade, ()):
        held += sum(cohort[1])
    return held


def _take_from(state: MarketState, area: str, trade: str, people: float) -> List[float]:
    """Remove `people` of the trade from an area in proportion to its bands; the bands taken."""
    bands = state.workers[area][trade]
    total = sum(bands)
    share = min(1.0, people / total) if total > 0.0 else 0.0
    taken = [count * share for count in bands]
    for band, amount in enumerate(taken):
        bands[band] -= amount
    return taken


def form_trades(state: MarketState, inputs: YearInputs, clearings, report: YearReport) -> None:
    """Fill empty trades' vacancies by migration and bonded purchase; record them in `report.formed`."""
    index = clearings if isinstance(clearings, dict) else index_clearings(clearings)
    hours_per_worker = inputs.hours_per_worker_year
    if hours_per_worker <= 0.0:
        return
    empty: List[Tuple[str, str, float]] = []
    for (area, trade), clearing in sorted(index.items()):
        wanted = clearing.vacant_hours / hours_per_worker
        if wanted > 0.0 and _held(state, area, trade) <= 0.0:
            empty.append((area, trade, wanted))
    for area, trade, wanted in empty:
        spare: Dict[str, float] = {}
        for origin in sorted(inputs.routes):
            if origin == area or not any(route.destination == area for route in inputs.routes[origin]):
                continue
            held = sum(state.workers.get(origin, {}).get(trade, ()))
            if held <= 0.0:
                continue
            origin_clearing = index.get((origin, trade))
            bid_hours = origin_clearing.hours_wanted if origin_clearing is not None else 0.0
            spare[origin] = spare_people(held, bid_hours, hours_per_worker)
        for_sale = inputs.bonded_for_sale.get(area, {}).get(trade, 0.0)
        takes = [("migration", origin, people) for origin, people in migration_takes(wanted, spare)]
        bought = min(wanted - sum(people for _, _, people in takes),
                     bonded_available(area in inputs.bondage_allowed, for_sale))
        if bought > 0.0:
            takes.append(("bonded", "", bought))
        for kind, origin, people in takes:
            if kind == "migration":
                taken = _take_from(state, origin, trade, people)
            else:
                count = aptitude.band_count()
                taken = [people / count] * count   # the bought are not picked for ability
            destination = state.workers.setdefault(area, {}).setdefault(trade, [0.0] * len(taken))
            for band, amount in enumerate(taken):
                destination[band] += amount
            by_route = report.formed.setdefault(area, {}).setdefault(trade, {})
            by_route[kind] = by_route.get(kind, 0.0) + sum(taken)
