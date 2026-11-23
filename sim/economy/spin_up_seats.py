"""The places to learn a trade during the hidden spin-up (the rule sets' `spin_up_seats`). A trade teaches at once only
a share of its practising workers (sim/labour/market/training.py), so a trade the opening sized far too small regrows
over decades: through all of the hidden years its wage stays at several times a labourer's and what it makes stays
short. The cap is a friction of the path and not of the rest, where a trade trains its replacements well inside it.
Where the seats are open, anyone may learn any trade that has a labour market in their area while the economy settles,
each for the trade's training years, so the settled economy has its people in the trades it wants."""
from typing import Dict, Iterable, Mapping, Sequence, Tuple

from sim.labour.api import School

OPEN_SEATS_OWNER = "spin_up_seats"      # the seats of the hidden years belong to no actor


def by_masters(schools: Sequence[School], _settling: bool, _working_people_by_area: Mapping[str, float],
               _markets: Iterable[Tuple[str, str]]) -> Tuple[School, ...]:
    """The year's schools: beyond them a trade's places to learn are its masters'."""
    return tuple(schools)


def open_while_settling(schools: Sequence[School], settling: bool, working_people_by_area: Mapping[str, float],
                        markets: Iterable[Tuple[str, str]]) -> Tuple[School, ...]:
    """The year's schools and, in a hidden year, for each of `markets` (a trade and the labour area it has a market
    in) a seat for every working person of the area; in sorted order, none where the area has no working people."""
    if not settling:
        return tuple(schools)
    return tuple(schools) + tuple(School(OPEN_SEATS_OWNER, trade, area, working_people_by_area[area])
                                  for trade, area in sorted(set(markets)) if working_people_by_area.get(area, 0.0) > 0.0)


def working_people_by_area(households: Iterable[Tuple[str, float]]) -> Dict[str, float]:
    """{area: working people} over `households`, each (its labour area, its working people)."""
    totals: Dict[str, float] = {}
    for area, people in households:
        totals[area] = totals.get(area, 0.0) + people
    return totals


def markets_of(keys: Iterable[str], separator: str) -> Tuple[Tuple[str, str], ...]:
    """(trade, labour area) of each labour market key (the trade, the separator, the area)."""
    return tuple(tuple(key.split(separator, 1)) for key in keys if separator in key)
