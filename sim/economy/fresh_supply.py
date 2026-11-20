"""What a producer will take for a good that cannot be kept a year (bread, milk, a day's catch), under the clearing rule set.

Nothing can be held back for next year, so there is no stock to read (`stock_supply.StockCurve`). What stands in for it is
the making itself: the good is made through the year as it sells, and at a price under the one the producer expected
the dearer of its workplaces stop. So at the expected price or more it lets everything go, and under it the share its
workplaces would still make at that price (`producers.share_working`, the same spread of workplace costs the labour bids
read) over the share they make at the expected price. What is not let go is lost: the hands were already hired."""
from dataclasses import dataclass

from .producers import share_working
from .types import Offer


@dataclass(frozen=True)
class FreshCurve:
    """One producer's supply of a good it cannot keep: the offer it posted (all it made) and the price it expected."""
    offer: Offer
    expected_price: float

    def supply_at(self, price: float) -> float:
        """Units let go at a price: all of the offer at the expected price or above, less under it."""
        if price >= self.expected_price:
            return self.offer.quantity
        return self.offer.quantity * share_working(price, self.expected_price) / share_working(1.0, 1.0)

    @property
    def content_price(self) -> float:
        """The price at which the seller is content to let go all it made: the one it expected (`StockCurve.content_price`'s twin)."""
        return self.expected_price

    @property
    def lowest_price(self) -> float:
        """The price under which next to nothing is let go: none above nothing (the share falls off smoothly)."""
        return 0.0

    @property
    def asking_price(self) -> float:
        """What the seller asks for a unit nobody bought: the price it expected (`StockCurve.asking_price`'s twin)."""
        return self.expected_price

    @property
    def highest_price(self) -> float:
        """The price at which everything is let go."""
        return self.expected_price

    def offer_at(self, price: float) -> Offer:
        """The seller's offer in a market that trades at `price`: the units it lets go at it, at that price (at the
        expected price where the market trades above it)."""
        offer = self.offer
        return Offer(offer.seller, offer.good, offer.area, offer.tile, self.supply_at(price), min(price, self.highest_price))
