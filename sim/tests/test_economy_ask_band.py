"""Complaint 643: a seller's ask is anchored on what a unit costs it. A sold-out seller's ask rises within a
band above that cost and stops at its edge; demand that does not respond to price gives a finite ask; only a
sole owner (one workshop) searches the buyers' book for its best ask."""

QUICK_TOPIC = True

import math
import types
import unittest

from sim.economy import ask_adjust, seller_offers
from sim.economy.producers import Producer
from sim.economy.types import Bid, Offer, Recipe

GOOD, AREA, TILE = "alloy", "area", "tile"
COST = 2.0 * 3.0 + 4.0 * 0.5      # two of metal at three, four hours at half


class View:
    year = 3

    def interest_rate(self, currency):
        return 0.0

    def currency_of(self, area):
        return "coin"

    def price(self, good, area):
        return {"metal": 3.0}.get(good)

    def wage(self, trade, area):
        return 0.5

    def area_of(self, good, tile):
        return AREA

    def stock(self, agent, good, tile):
        return 0.0


def game(*sellers, substitution=1.0):
    recipe = Recipe("melt", {GOOD: 1.0}, {"metal": 2.0}, {"labour": 4.0})
    producers = {name: Producer(name, "lord", "melt", TILE, 10.0) for name in sellers}
    basket = types.SimpleNamespace(substitution=substitution)
    setup = types.SimpleNamespace(specs={}, recipes={"melt": recipe}, basket_for=lambda tile: basket)
    return setup, types.SimpleNamespace(producers=producers, memory=types.SimpleNamespace(volume_weights={GOOD + "|" + AREA: 100.0}), unmet={})


def floor_buyer(quantity=100.0):
    """Takes `quantity` whatever the price: demand that does not respond."""
    return Bid("buyer", GOOD, AREA, TILE, quantity, 0.0, 10.0 * COST, 0.0, 1e12)


class SoldOutRaiseTests(unittest.TestCase):
    def test_a_sold_out_ask_rises_one_step_inside_the_band(self):
        raised = ask_adjust.adjusted_within_band(1.5 * COST, COST, 0.0, 1.0)
        self.assertAlmostEqual(raised, 1.5 * COST * (1.0 + ask_adjust.GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR))

    def test_a_sold_out_ask_stops_at_the_band_edge_however_many_years_it_sells_out(self):
        ask = COST
        for _year in range(500):
            ask = ask_adjust.adjusted_within_band(ask, COST, 0.0, 1.0)
        self.assertAlmostEqual(ask, COST * ask_adjust.ASK_BAND_CEILING)

    def test_an_ask_already_above_the_edge_is_not_cut_by_the_raise(self):
        self.assertEqual(ask_adjust.adjusted_within_band(10.0 * COST, COST, 0.0, 1.0), 10.0 * COST)

    def test_no_cost_to_anchor_on_means_no_raise(self):
        self.assertEqual(ask_adjust.adjusted_within_band(5.0, None, 0.0, 1.0), 5.0)
        self.assertEqual(ask_adjust.adjusted_within_band(5.0, math.inf, 0.0, 1.0), 5.0)


class InelasticBookTests(unittest.TestCase):
    def test_a_sole_owner_facing_unresponsive_demand_asks_a_finite_price_within_the_band(self):
        setup, record = game("only")
        ask = 1.2 * COST
        chosen = seller_offers.strategic_offers(setup, record, View(), [floor_buyer()],
                                                [Offer("only", GOOD, AREA, TILE, 100.0, ask)], 10.0)
        price = chosen[0].reservation_price
        self.assertTrue(math.isfinite(price))
        self.assertGreater(price, ask)       # a sole owner still prices strategically
        self.assertLessEqual(price, COST * ask_adjust.ASK_BAND_CEILING * (1.0 + 1e-9))

    def test_the_band_is_finite_for_every_elasticity_of_substitution(self):
        for substitution in (0.5, 1.0, 1.05, 3.0):
            setup, _record = game("only", substitution=substitution)
            multiple = seller_offers.ask_band_multiple(setup, Offer("only", GOOD, AREA, TILE, 1.0, 1.0))
            self.assertTrue(math.isfinite(multiple))
            self.assertGreater(multiple, 1.0)

    def test_an_aggregate_of_many_workshops_takes_the_price_and_does_not_search(self):
        setup, record = game("crowd")
        record.producers["crowd"] = Producer("crowd", "lord", "melt", TILE, 10.0, workshops=5)
        offers = [Offer("crowd", GOOD, AREA, TILE, 100.0, 1.2 * COST)]
        self.assertEqual(seller_offers.strategic_offers(setup, record, View(), [floor_buyer()], offers, 10.0), offers)


if __name__ == "__main__":
    unittest.main()
