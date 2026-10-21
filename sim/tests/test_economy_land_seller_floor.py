"""Complaint 538: a land seller's lowest acceptable price follows what the land yields its holder (the tile's rent
capitalised at the interest rate), not a queue of years behind a stock that never sells. Built inputs, the rule
(`unsold_search._held_value`) called directly."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import unsold_search
from sim.economy.producers import Producer
from sim.economy.types import GoodSpec, Offer, Recipe

LAND, AREA, TILE = "ground", "area", "tile"
RATE, OPENING_RATE, RENT, ASK = 0.15, 0.05, 6.0, 5000.0


class View:
    def __init__(self, rate=RATE):
        self.rate = rate

    def interest_rate(self, currency):
        return self.rate

    def currency_of(self, area):
        return "coin"


def held(stock, expected_sales, rent=RENT, rate=RATE, portable=True):
    spec = GoodSpec(LAND, 1.0 if portable else float("inf"), 0.0, 0.0, "land")
    recipe = Recipe("claim", {LAND: 1.0}, {}, {})
    setup = types.SimpleNamespace(specs={LAND: spec}, recipes={"claim": recipe}, opening_rate=OPENING_RATE)
    producer = Producer("seller", "lord", "claim", TILE, 10.0, expected_sales=expected_sales)
    record = types.SimpleNamespace(producers={"seller": producer}, land_rent={TILE: rent})
    return unsold_search._held_value(setup, record, View(rate), Offer("seller", LAND, AREA, TILE, stock, ASK))


class LandSellerFloorTests(unittest.TestCase):
    def test_a_stock_far_past_expected_sales_does_not_decay_the_floor_to_nothing(self):
        floor = held(stock=800.0, expected_sales=0.35, portable=False)
        self.assertGreater(floor, 0.5 * RENT / RATE)

    def test_the_floor_is_the_rent_over_the_rate_whatever_the_stock(self):
        self.assertAlmostEqual(held(10.0, 5.0, portable=False), held(1000.0, 0.1, portable=False))
        self.assertAlmostEqual(held(10.0, 5.0, portable=False), RENT / RATE)

    def test_a_rate_below_the_openings_capitalises_at_the_openings(self):
        self.assertAlmostEqual(held(10.0, 5.0, rate=0.01, portable=False), RENT / OPENING_RATE)

    def test_land_that_yields_no_rent_is_worth_nothing_to_hold(self):
        self.assertEqual(held(10.0, 5.0, rent=0.0, portable=False), 0.0)

    def test_a_portable_good_still_queues_behind_its_stock(self):
        self.assertLess(held(800.0, 0.35, portable=True), 1e-6)


if __name__ == "__main__":
    unittest.main()
