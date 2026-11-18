"""A seller's carried ask moves a step a year with its stock, a raise with no ceiling (the year's market finds the
price, unsold_search.py), and a producer takes the price in its market whether it stands for one workshop or many."""

QUICK_TOPIC = True

import math
import types
import unittest

from sim.tests.economy_view_defaults import ViewDefaults
from sim.economy import ask_adjust, seller_offers
from sim.economy.producers import Producer
from sim.economy.types import Bid, Offer, Recipe

GOOD, AREA, TILE = "alloy", "area", "tile"
COST = 2.0 * 3.0 + 4.0 * 0.5      # two of metal at three, four hours at half
STEP = ask_adjust.GOODS_ASK_ADJUSTMENT_SHARE_PER_YEAR


class View(ViewDefaults):
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
    setup = types.SimpleNamespace(specs={}, currency_id="coin", recipes={"melt": recipe}, basket_for=lambda tile: basket)
    return setup, types.SimpleNamespace(producers=producers, memory=types.SimpleNamespace(volume_weights={GOOD + "|" + AREA: 100.0}), goods=types.SimpleNamespace(unmet={}))


def floor_buyer(quantity=100.0):
    """Takes `quantity` whatever the price: demand that does not respond."""
    return Bid("buyer", GOOD, AREA, TILE, quantity, 0.0, 10.0 * COST, 0.0, 1e12)


class SoldOutRaiseTests(unittest.TestCase):
    def test_a_sold_out_ask_rises_one_step(self):
        self.assertAlmostEqual(ask_adjust.stepped_by_stock(1.5 * COST, COST, 0.0, 1.0), 1.5 * COST * (1.0 + STEP))

    def test_a_sold_out_ask_far_above_its_cost_still_rises_a_step(self):
        # no multiple of the cost stops it: what the buyers will pay is found when the market clears
        self.assertAlmostEqual(ask_adjust.stepped_by_stock(10.0 * COST, COST, 0.0, 1.0), 10.0 * COST * (1.0 + STEP))

    def test_no_cost_to_anchor_on_means_no_raise(self):
        self.assertEqual(ask_adjust.stepped_by_stock(5.0, None, 0.0, 1.0), 5.0)
        self.assertEqual(ask_adjust.stepped_by_stock(5.0, math.inf, 0.0, 1.0), 5.0)


class PriceTakerTests(unittest.TestCase):
    def test_a_producer_of_one_workshop_takes_the_price_and_does_not_search(self):
        setup, record = game("only")
        offers = [Offer("only", GOOD, AREA, TILE, 100.0, 1.2 * COST)]
        self.assertEqual(seller_offers.strategic_offers(setup, record, View(), [floor_buyer()], offers, 10.0), offers)

    def test_an_aggregate_of_many_workshops_takes_the_price_and_does_not_search(self):
        setup, record = game("crowd")
        record.producers["crowd"] = Producer("crowd", "lord", "melt", TILE, 10.0, workshops=5)
        offers = [Offer("crowd", GOOD, AREA, TILE, 100.0, 1.2 * COST)]
        self.assertEqual(seller_offers.strategic_offers(setup, record, View(), [floor_buyer()], offers, 10.0), offers)


if __name__ == "__main__":
    unittest.main()
