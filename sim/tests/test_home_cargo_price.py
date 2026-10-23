"""Cargo bound for home is sized by the home market's own price response (Complaints/115): the quote is a
summarised book re-cleared with one more order."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

import math

from sim.economy import goods_market, market_curves
from sim.economy.api import EDGE_EXTERNAL
from sim.economy.types import Bid, Offer

buyers = [Bid("a%d" % number, "grain", "area", "tile", 20.0, 40.0, 10.0, 1.5, 5000.0) for number in range(6)]
buyers += [Bid("b%d" % number, "grain", "area", "tile", 0.0, 30.0, 14.0, 0.8, 5000.0, 0, 30.0) for number in range(4)]
sellers = [Offer("s%d" % number, "grain", "area", "tile", 60.0, 4.0 + number) for number in range(8)]
curve = market_curves.summarize(buyers, sellers)
check("a book is summarised into a few rows, not one per order", len(curve["bids"]) <= 2 and len(curve["offers"]) <= 8,
      (len(curve["bids"]), len(curve["offers"])))
base = goods_market.clear(buyers, sellers, "grain", "area", "", None)
for landed, taken in ((30.0, 0.0), (120.0, 0.0), (0.0, 30.0), (0.0, 90.0)):
    quoted = market_curves.price_response(curve, "grain", None, landed, taken)
    extra_offers = sellers + ([Offer("x", "grain", "area", "tile", landed, 0.0)] if landed else [])
    extra_bids = buyers + ([Bid("y", "grain", "area", "tile", taken, 0.0, 0.0, 0.0, math.inf)] if taken else [])
    cleared = goods_market.clear(extra_bids, extra_offers, "grain", "area", "", base.price).price / base.price
    check("the quote for %g landed and %g taken matches the book clearing with it" % (landed, taken),
          quoted is not None and abs(quoted / cleared - 1.0) < 0.05, (quoted, cleared))
more_supply = market_curves.price_response(curve, "grain", None, 120.0, 0.0)
more_demand = market_curves.price_response(curve, "grain", None, 0.0, 90.0)
check("supply landing lowers the price and demand taking raises it", more_supply < 1.0 < more_demand, (more_supply, more_demand))
check("a market that traded nothing has no answer",
      market_curves.price_response({"bids": [], "offers": [[1.0, 5.0]]}, "grain", None, 10.0, 0.0) is None)
check("the external edge's own orders are not part of the summarised book",
      market_curves.summarize([Bid(EDGE_EXTERNAL, "g", "a", "t", 1.0, 0.0, 0.0, 0.0, 1.0)], []) == {"bids": [], "offers": []})

_landed_quotes = [market_curves.price_response(curve, "grain", None, tonnes, 0.0) for tonnes in (10.0, 1000.0, 100000.0)]
_taken_quotes = [market_curves.price_response(curve, "grain", None, 0.0, tonnes) for tonnes in (10.0, 1000.0, 100000.0)]
check("more cargo landed pushes the quote down further, never below zero",
      _landed_quotes[0] >= _landed_quotes[1] >= _landed_quotes[2] > 0.0, _landed_quotes)
check("more cargo taken pushes the quote up further", _taken_quotes[0] <= _taken_quotes[1] <= _taken_quotes[2], _taken_quotes)
_no_cargo = market_curves.price_response(curve, "grain", None, 0.0, 0.0)
check("with no extra cargo the quote is the market's price", _no_cargo is not None and abs(_no_cargo - 1.0) < 1e-9, _no_cargo)
