"""The plain-Python path of `labour_supply.HourSupply`, for a supply whose plot rule is not the parametric one.

A plot rule that is a bare function of the wage (a caller's own, or a mod's replacement of the rule behind
`household_hours_year.plot_schedule`) has no columns to put in the `LabourOffers` table, so the supply is summed offer by offer
here. The result is the same rule, with Python's `sum`; the table path and its kernels are used whenever every plot has
parameters. A mod that replaces the fetched-hands kernel (`markets.fetch_wage`) does not come here: the core then calls the
table's schedules (`labour_supply_markets.MarketHours`) one wage at a time."""
from typing import Callable, Dict, List, Mapping, Sequence, Tuple

from .types import LabourOffer


def hours_over(held, in_market: Sequence[LabourOffer]) -> Callable[[float], float]:
    """The hours sold at a wage by these offers: the sum of their schedules."""
    schedules = [held.sold_hours_schedule(offer) for offer in in_market if offer.hours > 0.0]

    def hours(wage: float) -> float:
        return sum([schedule(wage) for schedule in schedules])
    return hours


def schedules(held) -> Dict[Tuple[str, str], Callable[[float], float]]:
    """`hours_over` for every market that has an offer."""
    by_market: Dict[Tuple[str, str], List[LabourOffer]] = {}
    for offer in held.offers:
        by_market.setdefault((offer.trade, offer.area), []).append(offer)
    return {market: hours_over(held, by_market[market]) for market in sorted(by_market)}


def settle(held, wage_by_market: Mapping[Tuple[str, str], float]) -> List[LabourOffer]:
    """The offers as sold at the wages the markets cleared at (the faced wage where one did not); fills `held.kept`."""
    held.sold, held.kept = [], {}
    for offer in held.offers:
        market = (offer.trade, offer.area)
        wage = wage_by_market.get(market, held.faced_wage.get(market, offer.reservation_wage))
        sold, _at_home = held.split(offer, wage)
        held.sold.append(LabourOffer(offer.worker, offer.trade, offer.area, sold, offer.reservation_wage))
        held.kept[offer.worker] = held.kept.get(offer.worker, 0.0) + (offer.hours - sold)
    return held.sold
