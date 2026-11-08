"""The bids that later respend rounds add to a market, kept as columns (no `Bid` per bid; objects are built only at an edge).

`goods_respend_unpack.write_markets` hands a market the rows of its added bids as column slices of the respend kernel's log. A
reader asks for the numbers it needs (`quantities_at`, `columns`) or, for a rule still written over objects, `bids`.

Columns (one entry per added bid, in the order the kernel added them):
    buyer       household that bid                                           agent name
    tile        the household's tile                                          tile name
    flexible    units the bid would take beyond the floor (the floor is zero)  units
    reference   price the flexible units are quoted at                         currency per unit
    elasticity  the buyer's basket substitution                                 pure number
    budget      money the bid may spend                                         currency units
    maximum     highest price the bid accepts                                    currency per unit
"""
from typing import List, Sequence

from .goods_market import _quantity
from .goods_respend import RESPEND_PRIORITY
from .types import Bid


class AddedBids:
    """The added bids of one market (see the module docstring)."""

    def __init__(self, good: str, area: str, buyer: Sequence[str], tile: Sequence[str], flexible: Sequence[float],
                 reference: Sequence[float], elasticity: Sequence[float], budget: Sequence[float], maximum: Sequence[float]):
        self.good, self.area = good, area
        self.buyer, self.tile = list(buyer), list(tile)
        self.flexible, self.reference, self.elasticity = list(flexible), list(reference), list(elasticity)
        self.budget, self.maximum = list(budget), list(maximum)

    def __len__(self) -> int:
        return len(self.buyer)

    def quantities_at(self, price: float) -> List[float]:
        """`goods_market.quantity_at` of each added bid at a positive price: zero for no budget or a price above the bid's ceiling."""
        return [0.0 if budget <= 0.0 or price > ceiling else _quantity(0.0, flexible, reference, elasticity, budget, price)
                for flexible, reference, elasticity, budget, ceiling in zip(self.flexible, self.reference, self.elasticity, self.budget,
                                                                            self.maximum)]

    def bids(self) -> List[Bid]:
        """The added bids as `Bid` objects (an edge: a rule still written over objects, a test)."""
        return [Bid(buyer, self.good, self.area, tile, 0.0, flexible, reference, elasticity, budget, RESPEND_PRIORITY, maximum_price=ceiling)
                for buyer, tile, flexible, reference, elasticity, budget, ceiling in zip(
                    self.buyer, self.tile, self.flexible, self.reference, self.elasticity, self.budget, self.maximum)]
