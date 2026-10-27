"""The kernel behind `ImportCosts.wage`: the lowest wage at which hands fetched from other areas fill a shortage.

A plain function of plain inputs (numbers, lists and three lookups), so a mod can swap in a faster one (Complaint 661).
`hours_at`, `wanted_at` and `spare_of` are lookups the caller answers from its memos, so a replacement keeps them."""
from typing import Callable, List, Optional, Sequence, Tuple

BISECTION_STEPS = 40      # a numerical bound: the search for the wage at which fetched hands fill a shortage

HoursAt = Callable[[str, float], float]                              # (area, wage) -> hours the trade's workers there sell
SpareOf = Callable[[Sequence[str]], Tuple[List[float], float]]       # sources -> (each one's most spare hours, their sum)


def fills(area: str, sources: Sequence[str], wanted: float, wage: float, hours_at: HoursAt,
          wanted_at: Callable[[str], float], spare_of: SpareOf) -> bool:
    """Whether the hours sold here and fetched from `sources` at a wage reach `wanted`. The sources are added in
    turn and the count stops as soon as the answer cannot change: filled, or short even if every source still to
    come gave all it could."""
    own = hours_at(area, wage)
    remaining, to_come = spare_of(sources)
    slack = 1e-9 * (1.0 + abs(wanted))
    if own + to_come < wanted - slack:
        return False
    fetched = 0.0
    for other, cap in zip(sources, remaining):
        to_come -= cap
        fetched += max(0.0, hours_at(other, wage) - wanted_at(other))
        if own + fetched >= wanted:
            return True
        if own + fetched + to_come < wanted - slack:
            return False
    return own + fetched >= wanted


def lowest_filling(area: str, sources: Sequence[str], wanted: float, low: float, high: float, hours_at: HoursAt,
                   wanted_at: Callable[[str], float], spare_of: SpareOf) -> float:
    """The lowest wage in (low, high] at which the hours sold here and fetched from `sources` fill `wanted`,
    found by bisection on a total that rises with the wage; `high` fills it."""
    for _step in range(BISECTION_STEPS):
        middle = (low + high) / 2.0
        if fills(area, sources, wanted, middle, hours_at, wanted_at, spare_of):
            high = middle
        else:
            low = middle
    return high


def fetch_wage(area: str, wanted: float, going: float, top: float, offers: Callable[[], List[Tuple[float, str]]],
               hours_at: HoursAt, wanted_at: Callable[[str], float], spare_of: SpareOf) -> Optional[float]:
    """The wage an hour of the trade in `area` can be had for by fetching hands from elsewhere.

    `wanted` is the hours bid for here, `going` the wage now paid here, `top` the highest wage any bid would pay.
    `offers()` lists (wage an area's hands come at, area) for every other area that has a wage for the trade, in any
    order; `hours_at(area, wage)` the hours the trade's workers in an area sell at a wage (rising in it);
    `wanted_at(area)` the hours bid for in an area; `spare_of(sources)` each source's most spare hours and their sum.
    None where the workers on the spot sell enough at the going wage, or the spare hands do not fill the shortage:
    the bids then set the wage."""
    if hours_at(area, going) >= wanted:
        return None
    sources: List[str] = []
    lowest = going
    for cost, other in sorted(offers()):
        # more sources never sell fewer hours, so the sources so far fill it only if they and the next do
        if fills(area, sources + [other], wanted, cost, hours_at, wanted_at, spare_of):
            if fills(area, sources, wanted, cost, hours_at, wanted_at, spare_of):
                return lowest_filling(area, sources, wanted, lowest, cost, hours_at, wanted_at, spare_of)
            return cost
        sources.append(other)
        lowest = cost
    # past the dearest way in, a higher wage still draws more of the hours the workers keep back
    if top > lowest and fills(area, sources, wanted, top, hours_at, wanted_at, spare_of):
        return lowest_filling(area, sources, wanted, lowest, top, hours_at, wanted_at, spare_of)
    return None
