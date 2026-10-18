"""Complaint 550: a producer that stands for many independent workshops (each newcomer to a recipe on a tile
joins it) is a price taker, so splitting it into many identical small producers leaves the clearing price and
quantity where they were; a producer that is one owner's single workshop still prices strategically."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import goods_market, seller_offers, seller_pricing
from sim.economy.producers import Producer
from sim.economy.types import Bid, Offer, Recipe

GOOD, AREA, TILE = "grain", "area", "tile"
SHOPS = 20
TOTAL = 1000.0
ASK = 1.0


class View:
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
    setup = types.SimpleNamespace(recipes={"farm": recipe}, basket_for=lambda tile: basket)
    return setup, types.SimpleNamespace(producers={each.agent_id: each for each in producers})


def producer(name, workshops):
    return Producer(name, "owner:" + name, "farm", TILE, TOTAL, workshops=workshops)


def cleared(producers, quantities, bids=None):
    bids = bids or demand()
    setup, record = game(producers)
    offers = [Offer(each.agent_id, GOOD, AREA, TILE, quantity, ASK) for each, quantity in zip(producers, quantities)]
    chosen = seller_offers.strategic_offers(setup, record, View(), bids, offers, 1.0)
    result = goods_market.clear(bids, chosen, GOOD, AREA, "", 1.0)
    sold = sum(fill.quantity for fill in result.fills if fill.side == "sell")
    return result.price, sold


def mean_reservation(chosen):
    """The quantity-weighted reservation of an aggregate's slices."""
    return sum(each.reservation_price * each.quantity for each in chosen) / sum(each.quantity for each in chosen)


class AggregateProducerTests(unittest.TestCase):
    def test_splitting_an_aggregate_into_identical_small_producers_leaves_price_and_quantity(self):
        aggregate_price, aggregate_sold = cleared([producer("whole", SHOPS)], [TOTAL], deep_demand())
        small = [producer("shop%02d" % number, 1) for number in range(SHOPS)]
        split_price, split_sold = cleared(small, [TOTAL / SHOPS] * SHOPS, deep_demand())
        self.assertAlmostEqual(aggregate_price, split_price, delta=0.02 * split_price)
        self.assertAlmostEqual(aggregate_sold, split_sold, delta=0.02 * split_sold)

    def test_a_single_workshop_producer_still_prices_strategically(self):
        price, _sold = cleared([producer("only", 1)], [TOTAL])
        self.assertGreater(price, ASK * 1.05)

    def test_an_aggregate_keeps_the_price_taking_ask(self):
        setup, record = game([producer("whole", SHOPS)])
        chosen = seller_offers.strategic_offers(setup, record, View(), deep_demand(),
                                                [Offer("whole", GOOD, AREA, TILE, TOTAL, ASK)], 1.0)
        self.assertAlmostEqual(mean_reservation(chosen), ASK)
        self.assertAlmostEqual(sum(each.quantity for each in chosen), TOTAL)

    def test_an_aggregate_with_unsold_stock_above_its_cost_marks_its_ask_down_by_the_share_unsold(self):
        setup, record = game([producer("whole", SHOPS)])
        chosen = seller_offers.strategic_offers(setup, record, View(), demand(),
                                                [Offer("whole", GOOD, AREA, TILE, TOTAL, 10.0)], 1.0)
        buyers = goods_market.Buyers(demand(), 1.0)
        sold, _price = seller_pricing.sold_and_price(demand(), [], Offer("whole", GOOD, AREA, TILE, TOTAL, 10.0), 10.0, 1.0, buyers)
        unsold_share = 1.0 - sold / TOTAL
        self.assertGreater(unsold_share, 0.0)
        cost = seller_offers.unit_cost(setup, record, View(), Offer("whole", GOOD, AREA, TILE, TOTAL, 10.0))
        self.assertAlmostEqual(mean_reservation(chosen), 10.0 - unsold_share * (10.0 - cost))

    def test_a_mostly_sold_aggregate_marks_down_by_less_than_a_full_step(self):
        setup, record = game([producer("whole", SHOPS)])
        bids = [Bid("buyer", GOOD, AREA, TILE, 0.9 * TOTAL, 0.0, 1.0, 0.5, 1e9)]
        chosen = seller_offers.strategic_offers(setup, record, View(), bids,
                                                [Offer("whole", GOOD, AREA, TILE, TOTAL, 10.0)], 1.0)
        self.assertGreater(mean_reservation(chosen), 9.0)
        self.assertLess(mean_reservation(chosen), 10.0)

    def test_an_aggregate_whose_stock_goes_unsold_at_a_high_ask_comes_down_to_its_cost(self):
        setup, record = game([producer("whole", SHOPS)])
        cost = seller_offers.unit_cost(setup, record, View(), Offer("whole", GOOD, AREA, TILE, TOTAL, 5.0))
        nobody_buys = [Bid("buyer", GOOD, AREA, TILE, 0.0, 0.0, 1.0, 1.0, 0.0)]
        chosen = seller_offers.strategic_offers(setup, record, View(), nobody_buys,
                                                [Offer("whole", GOOD, AREA, TILE, TOTAL, 5.0 * cost)], 1.0)
        self.assertAlmostEqual(mean_reservation(chosen), cost)

    def test_an_aggregate_offers_a_rising_schedule_over_its_workshops_costs(self):
        setup, record = game([producer("whole", SHOPS)])
        chosen = seller_offers.strategic_offers(setup, record, View(), deep_demand(),
                                                [Offer("whole", GOOD, AREA, TILE, TOTAL, ASK)], 1.0)
        asks = [each.reservation_price for each in sorted(chosen, key=lambda each: each.reservation_price)]
        self.assertGreater(len(asks), 2)
        self.assertEqual(asks, sorted(set(asks)))

    def test_a_larger_order_from_an_aggregate_pays_more_per_unit(self):
        def per_unit(wanted):
            setup, record = game([producer("whole", SHOPS)])
            bids = [Bid("buyer", GOOD, AREA, TILE, wanted, 0.0, 1.0, 0.5, 1e9)]
            chosen = seller_offers.strategic_offers(setup, record, View(), bids,
                                                    [Offer("whole", GOOD, AREA, TILE, TOTAL, ASK)], 1.0)
            return goods_market.clear(bids, chosen, GOOD, AREA, "", 1.0).price
        self.assertGreater(per_unit(0.9 * TOTAL), per_unit(0.1 * TOTAL))

    def test_a_sale_into_an_aggregate_lowers_the_price(self):
        setup, record = game([producer("whole", SHOPS)])
        bids = [Bid("buyer", GOOD, AREA, TILE, 0.6 * TOTAL, 0.0, 1.0, 0.5, 1e9)]
        chosen = seller_offers.strategic_offers(setup, record, View(), bids,
                                                [Offer("whole", GOOD, AREA, TILE, TOTAL, ASK)], 1.0)
        alone = goods_market.clear(bids, chosen, GOOD, AREA, "", 1.0).price
        founder = Offer("founder", GOOD, AREA, TILE, 0.3 * TOTAL, 0.0)
        with_founder = goods_market.clear(bids, chosen + [founder], GOOD, AREA, "", 1.0).price
        self.assertLess(with_founder, alone)


if __name__ == "__main__":
    unittest.main()
