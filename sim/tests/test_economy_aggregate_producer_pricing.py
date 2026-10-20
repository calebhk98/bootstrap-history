"""Complaint 550: a producer that stands for many independent workshops (each newcomer to a recipe on a tile
joins it) is a price taker, so splitting it into many identical small producers leaves the clearing price and
quantity where they were; a producer that is one owner's single workshop still prices strategically."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import goods_market, seller_offers, unsold_search
from sim.economy.producers import Producer
from sim.economy.types import Bid, Offer, Recipe

GOOD, AREA, TILE = "grain", "area", "tile"
SHOPS = 20
TOTAL = 1000.0
ASK = 1.0


class View:
    def interest_rate(self, currency):
        return 0.0

    def currency_of(self, area):
        return "coin"

    year = 3

    def price(self, good, area):
        return {"seed": 0.1}.get(good)

    def wage(self, trade, area):
        return 0.1

    def area_of(self, good, tile):
        return AREA

    def stock(self, agent, good, tile):
        return 0.0


def demand():
    """One buyer whose want falls with price, around a reference price of one."""
    return [Bid("buyer", GOOD, AREA, TILE, 0.0, 800.0, 1.0, 0.5, 600.0)]


def deep_demand():
    """Buyers who take everything on offer at the ask, so no stock goes unsold."""
    return [Bid("buyer", GOOD, AREA, TILE, 2.0 * TOTAL, 0.0, 1.0, 0.5, 1e9)]


def game(producers):
    recipe = Recipe("farm", {GOOD: 1.0}, {"seed": 1.0}, {"labour": 1.0})
    basket = types.SimpleNamespace(substitution=1.0)
    setup = types.SimpleNamespace(specs={}, recipes={"farm": recipe}, basket_for=lambda tile: basket)
    return setup, types.SimpleNamespace(producers={each.agent_id: each for each in producers})


def producer(name, workshops):
    return Producer(name, "owner:" + name, "farm", TILE, TOTAL, workshops=workshops)


def cleared(producers, quantities, bids=None, ask=ASK):
    bids = bids or demand()
    setup, record = game(producers)
    offers = [Offer(each.agent_id, GOOD, AREA, TILE, quantity, ask) for each, quantity in zip(producers, quantities)]
    chosen = seller_offers.strategic_offers(setup, record, View(), bids, offers, 1.0)
    result = goods_market.clear(bids, chosen, GOOD, AREA, "", 1.0)
    sold = sum(fill.quantity for fill in result.fills if fill.side == "sell")
    return result.price, sold


class AggregateProducerTests(unittest.TestCase):
    def test_splitting_an_aggregate_into_identical_small_producers_leaves_price_and_quantity(self):
        aggregate_price, aggregate_sold = cleared([producer("whole", SHOPS)], [TOTAL], deep_demand())
        small = [producer("shop%02d" % number, 1) for number in range(SHOPS)]
        split_price, split_sold = cleared(small, [TOTAL / SHOPS] * SHOPS, deep_demand())
        self.assertAlmostEqual(aggregate_price, split_price, delta=0.02 * split_price)
        self.assertAlmostEqual(aggregate_sold, split_sold, delta=0.02 * split_sold)

    def test_a_single_workshop_producer_still_prices_strategically(self):
        setup, record = game([producer("only", 1)])
        cost = seller_offers.unit_cost(setup, record, View(), Offer("only", GOOD, AREA, TILE, TOTAL, ASK))
        ask = 1.5 * cost
        price, _sold = cleared([producer("only", 1)], [TOTAL], ask=ask)
        self.assertGreater(price, ask)     # it raises its ask against the residual demand, within the band
        self.assertLessEqual(price, cost * seller_offers.ASK_BAND_CEILING * (1.0 + 1e-9))

    def test_an_aggregate_keeps_the_price_taking_ask(self):
        setup, record = game([producer("whole", SHOPS)])
        chosen = seller_offers.strategic_offers(setup, record, View(), deep_demand(),
                                                [Offer("whole", GOOD, AREA, TILE, TOTAL, ASK)], 1.0)
        self.assertEqual(chosen[0].reservation_price, ASK)

    def test_an_aggregate_with_unsold_stock_above_its_cost_is_brought_down_to_what_sells_within_the_year(self):
        setup, record = game([producer("whole", SHOPS)])
        offers = [Offer("whole", GOOD, AREA, TILE, TOTAL, 10.0)]
        chosen = seller_offers.strategic_offers(setup, record, View(), demand(), offers, 1.0)
        final, result = unsold_search.clear_with_search(setup, record, View(), demand(), offers, chosen, GOOD, AREA, "", 1.0)
        cost = seller_offers.unit_cost(setup, record, View(), offers[0])
        self.assertLess(final[0].reservation_price, 10.0)
        self.assertGreaterEqual(final[0].reservation_price, cost)
        self.assertGreater(result.quantity, 0.0)

    def test_stock_buyers_cannot_absorb_even_at_the_floor_ends_at_the_cost(self):
        setup, record = game([producer("whole", SHOPS)])
        bids = [Bid("buyer", GOOD, AREA, TILE, 0.9 * TOTAL, 0.0, 1.0, 0.5, 1e9)]
        offers = [Offer("whole", GOOD, AREA, TILE, TOTAL, 10.0)]
        final, _result = unsold_search.clear_with_search(setup, record, View(), bids, offers, offers, GOOD, AREA, "", 1.0)
        cost = seller_offers.unit_cost(setup, record, View(), offers[0])
        self.assertAlmostEqual(final[0].reservation_price, cost)

    def test_an_aggregate_whose_stock_goes_unsold_at_a_high_ask_comes_down_to_its_cost(self):
        setup, record = game([producer("whole", SHOPS)])
        cost = seller_offers.unit_cost(setup, record, View(), Offer("whole", GOOD, AREA, TILE, TOTAL, 5.0))
        nobody_buys = [Bid("buyer", GOOD, AREA, TILE, 0.0, 0.0, 1.0, 1.0, 0.0)]
        offers = [Offer("whole", GOOD, AREA, TILE, TOTAL, 5.0 * cost)]
        final, _result = unsold_search.clear_with_search(setup, record, View(), nobody_buys, offers, offers, GOOD, AREA, "", 1.0)
        self.assertAlmostEqual(final[0].reservation_price, cost)


if __name__ == "__main__":
    unittest.main()
