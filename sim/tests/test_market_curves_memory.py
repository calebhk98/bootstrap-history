"""A repeated quote on one book gives the same answer as a first quote, and a changed book is not answered from memory."""
from .harness import *  # noqa: F401,F403

from sim.economy import market_curves
from sim.economy.types import Bid, Offer

QUICK_TOPIC = True

buyers = [Bid("a%d" % number, "grain", "area", "tile", 20.0, 40.0, 10.0, 1.5, 5000.0) for number in range(6)]
sellers = [Offer("s%d" % number, "grain", "area", "tile", 60.0, 4.0 + number) for number in range(8)]
curve = market_curves.summarize(buyers, sellers)

market_curves._BASE_CLEARINGS.clear()
first = market_curves.price_response(curve, "grain", None, 5.0, 0.0)
again = market_curves.price_response(curve, "grain", None, 5.0, 0.0)
check("a repeated quote on one book is identical", first == again and first is not None, (first, again))
other = market_curves.price_response(curve, "grain", None, 5.0, 20.0)
market_curves._BASE_CLEARINGS.clear()
check("a quote answered from memory equals one computed fresh",
      other == market_curves.price_response(curve, "grain", None, 5.0, 20.0), other)
curve["bids"][0][4] *= 0.001
changed = market_curves.price_response(curve, "grain", None, 5.0, 0.0)
market_curves._BASE_CLEARINGS.clear()
check("a changed book is not answered from memory",
      changed == market_curves.price_response(curve, "grain", None, 5.0, 0.0), (changed, first))
