"""Trader route rules (Complaints/115, 529), on a world the test builds: a cargo is sized by the price it makes, and a
good is only carried to a place that has a market for it."""
from .harness import *  # noqa: F401,F403

from sim.agents.trader import depth_room
from sim.agents.trader_routes import gaining_routes, paying_tonnes, price_answers, route_terms
from sim.agents.tuning_trader import TRADER_DEPTH_SHARE, TRADER_RISK_SHARE

QUICK_TOPIC = True


class PlainWorld:
    """Two places for one good. A price answers cargo linearly (a place in `book_slope`) or does not move (no book)."""

    def __init__(self, prices, freight=1.0, book_slope=None, markets=None, depth=100.0, delivered=0.0):
        self.prices = dict(prices)
        self.freight = freight
        self.book_slope = dict(book_slope or {})
        self.markets = set(markets if markets is not None else prices)
        self.depth = depth
        self.delivered = delivered

    def price_at(self, material, place):
        return self.prices.get(place)

    def freight_between(self, source, destination, material, tonnes):
        return self.freight

    def has_market(self, material, place):
        return place in self.markets

    def price_after_cargo(self, material, place, tonnes, landing):
        if place not in self.book_slope:
            return None
        move = self.book_slope[place] * tonnes
        return self.prices[place] - move if landing else self.prices[place] + move

    def market_depth(self, material, place):
        return self.depth

    def delivered_this_year(self, material, place):
        return self.delivered


RATE = 0.05


def pays(world, cargo):
    sold = world.price_after_cargo("grain", "far", cargo, True)
    bought = world.price_after_cargo("grain", "near", cargo, False)
    return sold - bought * (1.0 + TRADER_RISK_SHARE + RATE) - world.freight > 0.0


answering = PlainWorld({"near": 10.0, "far": 20.0}, book_slope={"near": 0.01, "far": 0.01})
terms = route_terms(answering, "near", "far", "grain")
check("a route's gain is the price gap less carriage and the share lost on the way",
      abs(terms["gain"] - (20.0 - 11.0 - 10.0 * TRADER_RISK_SHARE)) < 1e-9, terms)
check("a place with no price gives no route terms", route_terms(PlainWorld({"near": 10.0}), "near", "far", "grain") is None)

limit = paying_tonnes(answering, "near", "far", "grain", terms, 1e9, RATE)
check("a cargo sized against the price it makes still pays", limit > 0.0 and pays(answering, limit * 0.999), limit)
check("a quarter more cargo than the limit would not pay", not pays(answering, limit * 1.25), limit)
check("a cargo that fits under the limit is taken whole",
      paying_tonnes(answering, "near", "far", "grain", terms, limit * 0.5, RATE) == limit * 0.5)
check("no cargo is sized at nothing", paying_tonnes(answering, "near", "far", "grain", terms, 0.0, RATE) == 0.0)

# a dearer money rate narrows the cargo that pays
check("dearer money shrinks the cargo that pays",
      paying_tonnes(answering, "near", "far", "grain", terms, 1e9, 0.5) < limit)

check("a place with a book answers cargo; one without a book does not",
      price_answers(answering, "grain", "far") and not price_answers(PlainWorld({"near": 10.0, "far": 20.0}), "grain", "far"))

# no book: the cargo is limited by the share of the buyers' depth, less what has already arrived
bookless = PlainWorld({"near": 10.0, "far": 20.0}, depth=100.0, delivered=5.0)
check("without a book the room is a share of the buyers' depth less what has arrived",
      abs(depth_room(bookless, "near", "far", "grain") - (100.0 * TRADER_DEPTH_SHARE - 5.0)) < 1e-9,
      depth_room(bookless, "near", "far", "grain"))
check("planned cargo uses up the room, which never goes below nothing",
      depth_room(bookless, "near", "far", "grain", planned=1e6) == 0.0)

# traders ship only goods the destination has a market for (Complaints/529)
no_book_at_home = PlainWorld({"home": 10.0, "partner": 5.0}, freight=0.1, markets={"partner"})
routes = list(gaining_routes(no_book_at_home, "grain", ["home", "partner"], lambda place: ["home", "partner"]))
check("a good dearer at home than at the partner is not carried into a home with no market for it",
      all(destination != "home" for _source, destination, _terms in routes), routes)
with_book = PlainWorld({"home": 10.0, "partner": 5.0}, freight=0.1)
routes = list(gaining_routes(with_book, "grain", ["home", "partner"], lambda place: ["home", "partner"]))
check("...and is carried there once the home has a market for it",
      [(source, destination) for source, destination, _terms in routes] == [("partner", "home")], routes)
check("a gap too narrow to cover the share lost on the way gives no route",
      not list(gaining_routes(PlainWorld({"a": 10.0, "b": 10.1}, freight=0.0), "grain", ["a", "b"], lambda place: ["a", "b"])))
