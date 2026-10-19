"""Complaint 502: a producer's ask is held to what it costs to make times the markup a seller can charge when
buyers can substitute toward other goods meeting the same need. Against buyers who spend a fixed budget and
name no maximum price, a profit-maximiser would raise its ask every year without limit; an idle producer that
sells nothing at an ask far above that comes down to its cost within the year (unsold_search.py)."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import seller_offers, unsold_search
from sim.economy.producers import Producer
from sim.economy.types import Bid, Offer, Recipe

GOOD, AREA, TILE, SELLER = "alloy", "area", "tile", "producer:alloy"
SUBSTITUTION = 2.0
MARKUP = SUBSTITUTION / (SUBSTITUTION - 1.0)
RUN_COST_PER_UNIT = 2.0 * 3.0 + 4.0 * 0.5     # two of metal at three, four hours at half


class View:
    year = 3

    def price(self, good, area):
        return {"metal": 3.0}.get(good)

    def wage(self, trade, area):
        return 0.5

    def area_of(self, good, tile):
        return AREA

    def stock(self, agent, good, tile):
        return 0.0


def game(substitution=SUBSTITUTION):
    recipe = Recipe("melt", {GOOD: 1.0}, {"metal": 2.0}, {"labour": 4.0})
    producer = Producer(SELLER, "lord", "melt", TILE, 10.0)
    basket = types.SimpleNamespace(substitution=substitution)
    setup = types.SimpleNamespace(recipes={"melt": recipe}, basket_for=lambda tile: basket)
    record = types.SimpleNamespace(producers={SELLER: producer})
    return setup, record


def fixed_budget_buyer(budget=2000.0, reference=10.0):
    """A buyer with a sum to spend whatever the price: it takes budget over price and names no maximum."""
    return Bid("buyer", GOOD, AREA, TILE, 0.0, budget / reference, reference, 1.0, budget)


def offer(quantity, ask):
    return Offer(SELLER, GOOD, AREA, TILE, quantity, ask)


def asked(bids, quantity, ask, last_price, substitution=SUBSTITUTION):
    setup, record = game(substitution)
    chosen = seller_offers.strategic_offers(setup, record, View(), bids, [offer(quantity, ask)], last_price)
    return chosen[0].reservation_price


class MarkupLimitTests(unittest.TestCase):
    def test_a_fixed_budget_buyer_does_not_draw_the_ask_above_cost_times_the_markup(self):
        ask = asked([fixed_budget_buyer()], 1000.0, 0.97 * MARKUP * RUN_COST_PER_UNIT, 10.0)
        self.assertLessEqual(ask, MARKUP * RUN_COST_PER_UNIT * (1.0 + 1e-9))

    def test_an_idle_seller_far_above_the_limit_comes_down_to_its_cost_within_the_year(self):
        bids = [fixed_budget_buyer(budget=5.0, reference=200.0)]
        setup, record = game()
        offers = [offer(100.0, 200.0)]
        chosen = seller_offers.strategic_offers(setup, record, View(), bids, offers, 200.0)
        final, _result = unsold_search.clear_with_search(setup, record, View(), bids, offers, chosen, GOOD, AREA, "", 200.0)
        self.assertAlmostEqual(final[0].reservation_price, RUN_COST_PER_UNIT)

    def test_a_seller_that_sells_at_its_ask_above_the_limit_is_not_cut_by_the_hold(self):
        # a buyer who takes everything offered at the ask: the seller is not idle, so only the usual search applies
        eager = [Bid("buyer", GOOD, AREA, TILE, 500.0, 0.0, 200.0, 0.0, 1e9)]
        self.assertGreaterEqual(asked(eager, 100.0, 200.0, 200.0), 0.85 * 200.0)

    def test_without_substitution_there_is_no_limit(self):
        ask = asked([fixed_budget_buyer(budget=5.0, reference=200.0)], 100.0, 200.0, 200.0, substitution=1.0)
        self.assertGreaterEqual(ask, 0.85 * 200.0)


if __name__ == "__main__":
    unittest.main()
