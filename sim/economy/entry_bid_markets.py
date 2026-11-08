"""The markets with bids that the margin rule (entry_margin.py) and the trial rule (entry_trial.py) both walk, worked out once.

`weigh` goes over the year's bids block in market order and, for each market whose good some known recipe makes, reads the market area,
the output its makers could reach (`capacity`) and the price. The margin rule takes the markets with capacity, the trial rule those without;
what each does with them is theirs.

Columns of a `BidMarket`:
    good, area_id   the market
    place           its number in the bids block (`year_bids.YearBids`)
    area            the `MarketArea` of the good it sits in, or None when the area map has none by that id
    capacity        output of the good its makers could reach, plant to come counted; 0.0 without an area
    price           the market's price now (`view.price`); None without an area or when it has none
"""
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence

from .year_bids import YearBids


@dataclass(frozen=True)
class BidMarket:
    good: str
    area_id: str
    place: int
    area: Optional[object]
    capacity: float
    price: Optional[float]


def makers_of(recipes: Mapping[str, object]) -> Dict[str, List[str]]:
    """Per good, the ids of the recipes that make it, in sorted id order."""
    makers: Dict[str, List[str]] = {}
    for recipe_id in sorted(recipes):
        for good in recipes[recipe_id].outputs:
            makers.setdefault(good, []).append(recipe_id)
    return makers


def weigh(block: YearBids, makers: Mapping[str, Sequence[str]], area_map, view, capacity_in) -> List[BidMarket]:
    """The block's markets whose good has makers among the recipes and a place on the area map, in the block's (sorted) order.
    `capacity_in(good, area)` is `entry_trial.reachable_capacity`."""
    areas_of: Dict[str, Dict[str, object]] = {}
    known_goods = set(area_map.goods())
    weighed = []
    for place, (good, area_id) in enumerate(block.markets):
        if good not in makers or good not in known_goods:
            continue
        if good not in areas_of:
            areas_of[good] = {each.area_id: each for each in area_map.areas(good)}
        area = areas_of[good].get(area_id)
        if area is None:
            weighed.append(BidMarket(good, area_id, place, None, 0.0, None))
        else:
            weighed.append(BidMarket(good, area_id, place, area, capacity_in(good, area), view.price(good, area_id)))
    return weighed
