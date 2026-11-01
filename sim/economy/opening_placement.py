"""Placing the opening's people by the hours each sells, and holding contracts to the people placed.

A person sells the hours his household's plot, plan and household work leave (opening_own.OwnPlots), which differ
by area. The opening places people as hours wanted over the hours a person of that area sells, seeds a trade no
producer staffs only where a carriage channel hires it, and holds each trade's contracted hours to what its placed
people sell, so no contract is wider than the people who could work it (Complaints 556, 608, 960)."""
from typing import Dict, Mapping, Set, Tuple, Union

from sim.labour.api import bound_by_hirers

HoursPerWorker = Union[float, Mapping[str, float]]     # one figure for every area, or a figure per labour area
RELATIVE_SLACK = 1e-9     # a numerical bound: a contract this far over its people's hours is rounding, not a shortfall


def sold_hours_per_worker_by_area(sold_by_cohort: Mapping[str, float], cohort_rows: Mapping[str, Tuple[str, float]],
                                  default: float) -> Dict[str, float]:
    """Hours a working person sells a year in each labour area: the hours its cohorts sell over their working people.
    `cohort_rows[cohort] = (area, working people)`. An area whose people sell nothing or are none takes `default`
    (the figure over the whole society); a cohort with no sold figure sells nothing."""
    sold: Dict[str, float] = {}
    people: Dict[str, float] = {}
    for cohort_id in sorted(cohort_rows):
        area, working = cohort_rows[cohort_id]
        sold[area] = sold.get(area, 0.0) + sold_by_cohort.get(cohort_id, 0.0)
        people[area] = people.get(area, 0.0) + working
    return {area: sold[area] / people[area] if people[area] > 0.0 and sold[area] > 0.0 else default for area in sorted(people)}


def hours_per_worker_in(area: str, hours_per_worker: HoursPerWorker, default: float) -> float:
    """The hours a person sells in `area`: the mapping's figure for it, else `default`; a plain number is every area's."""
    if isinstance(hours_per_worker, Mapping):
        return hours_per_worker.get(area, 0.0) or default
    return hours_per_worker or default


def carriage_trades(setup) -> Set[str]:
    """The trades the setup's carriage hires crews in: each mode's crew trade (unskilled where it names none) and the
    trade that handles a change to a priced mode. None when carriage hires no hours."""
    trades: Set[str] = set()
    for trade, hours in setup.carriage_crew.values():
        if hours > 0.0:
            trades.add(trade or setup.unskilled_trade)
    for mode, hours in setup.carriage_handling.items():
        if hours > 0.0:
            trades.add(setup.carriage_handling_trade.get(mode) or setup.unskilled_trade)
    return trades


def seeds_where_hired(seeds_by_area: Mapping[str, Mapping[str, float]], hiring_trades: Set[str]
                      ) -> Dict[str, Dict[str, float]]:
    """The seeded hours of the trades some hirer asks (`hiring_trades`); the people of a trade nobody hires are not
    seeded and take up the fallback trade, and the plot trade with what no employer needs."""
    kept: Dict[str, Dict[str, float]] = {}
    for area, seeds in sorted(seeds_by_area.items()):
        hirers = {trade: (hours if trade in hiring_trades else 0.0) for trade, hours in seeds.items()}
        bounded = bound_by_hirers(seeds, hirers)
        if bounded:
            kept[area] = bounded
    return kept


def capped_contracts(held: Mapping[str, Mapping[str, Mapping[str, float]]],
                     people_by_area_and_trade: Mapping[str, Mapping[str, float]], hours_per_worker: HoursPerWorker,
                     default: float) -> Dict[str, Dict[str, Dict[str, float]]]:
    """`held` (area -> trade -> employer -> hours) with each (area, trade) cut, in proportion across its employers, to the
    hours its placed people sell: people times the hours a person of the area sells. A trade whose people sell as
    many hours as are contracted is unchanged."""
    capped: Dict[str, Dict[str, Dict[str, float]]] = {}
    for area, by_trade in sorted(held.items()):
        per_person = hours_per_worker_in(area, hours_per_worker, default)
        for trade, by_employer in sorted(by_trade.items()):
            room = people_by_area_and_trade.get(area, {}).get(trade, 0.0) * per_person
            wanted = sum(by_employer.values())
            factor = 1.0 if wanted <= room * (1.0 + RELATIVE_SLACK) else room / wanted
            for employer, hours in sorted(by_employer.items()):
                if hours * factor > 0.0:
                    capped.setdefault(area, {}).setdefault(trade, {})[employer] = hours * factor
    return capped
