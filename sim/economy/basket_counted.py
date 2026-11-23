"""How much of each good of the opening basket the fixed-basket price level counts (the rule sets'
`basket_quantity_counted`). The basket's quantities are what households bought at the opening. A good whose market
has since all but closed still trades now and then, a sliver at many times its opening price, and counted at its whole
opening quantity that price moves the level as if the whole basket were still bought at it. Counted by what its
markets usually trade, never more than the opening quantity, a market that trades as it did counts as before, one
that shrinks loses its weight as its usual volume falls, and a sliver moves the level by a sliver."""
from typing import Callable, Dict, Mapping

from .market_memory import KEY_SEPARATOR


def whole(opening_quantity: float, _usual_volume: float) -> float:
    """The good counts at its whole opening quantity, however little of it trades."""
    return opening_quantity


def still_bought(opening_quantity: float, usual_volume: float) -> float:
    """The good counts by what its markets usually trade, at most its opening quantity and never less than nothing."""
    return min(opening_quantity, max(0.0, usual_volume))


def usual_volume_by_good(volumes_by_market: Mapping[str, float]) -> Dict[str, float]:
    """{good: what its markets usually trade in a year}, summed over the market keys of `volumes_by_market`."""
    totals: Dict[str, float] = {}
    for key in sorted(volumes_by_market):
        good = key.split(KEY_SEPARATOR, 1)[0]
        totals[good] = totals.get(good, 0.0) + volumes_by_market[key]
    return totals


def counted(basket: Mapping[str, float], usual_by_good: Mapping[str, float],
            quantity_counted: Callable[[float, float], float]) -> Dict[str, float]:
    """{good: the quantity of it the price level counts} for the goods of `basket` ({good: opening quantity}) that
    `quantity_counted(opening quantity, usual volume)` leaves some of; a good no market of which is in
    `usual_by_good` usually trades nothing."""
    quantities = {good: quantity_counted(quantity, usual_by_good.get(good, 0.0)) for good, quantity in sorted(basket.items())}
    return {good: quantity for good, quantity in quantities.items() if quantity > 0.0}
