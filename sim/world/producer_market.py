"""What a producer offers: a quantity, and the lowest price it will sell at.

A producer's reservation price is what a unit costs it to make by the technique it runs, at the input
prices it pays (the engine works that out; the market only receives it, as a ratio to the market's
reference price). At a price below it the producer sells nothing, so it does not set the price and does
not add supply; at or above it the producer sells its quantity. The reservation can be negative: a
by-product that costs money to dispose of is sold at any price, and is never floored at zero.

Standalone: tonnes and ratios in, tonnes out. It knows nothing of how a cost came about.
"""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Offer:
    tonnes: float
    reservation_ratio: float


def offered_tonnes(offers: Iterable[Offer], price_ratio: float) -> float:
    """Tonnes producers are willing to sell at this price ratio."""
    return sum(offer.tonnes for offer in offers if price_ratio >= offer.reservation_ratio)
