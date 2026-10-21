"""Complaint 538: a land seller's lowest acceptable price follows what the land yields its holder (the tile's rent
capitalised at the interest rate), not a queue of years behind a stock that never sells. Built inputs, the rule
(`unsold_search._held_value`) called directly."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import unsold_search
from sim.economy.producers import Producer
from sim.economy.types import Bid, GoodSpec, Offer, Recipe

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


class AskFallsToTheCapitalisedRentTests(unittest.TestCase):
    """The year's search (unsold_search.clear_with_search) brings an unsold land ask down to the floor, the
    capitalised rent at the lowest, and sells out at what a buyer pays above it, whatever the stock and however few
    hectares are expected to sell."""

    def search(self, worth, stock=800.0, expected_sales=0.35):
        spec = GoodSpec(LAND, float("inf"), 0.0, 0.0, "land")
        setup = types.SimpleNamespace(specs={LAND: spec}, recipes={"claim": Recipe("claim", {LAND: 1.0}, {}, {})},
                                      opening_rate=OPENING_RATE)
        producer = Producer("seller", "lord", "claim", TILE, 10.0, expected_sales=expected_sales)
        record = types.SimpleNamespace(producers={"seller": producer}, land_rent={TILE: RENT})
        offer = Offer("seller", LAND, AREA, TILE, stock, ASK)
        bids = [Bid("buyer", LAND, AREA, TILE, 0.0, stock, worth, 0.0, 1e9, 1, maximum_price=worth)]
        offers, result = unsold_search.clear_with_search(setup, record, View(), bids, [offer], [offer], LAND, AREA,
                                                         "coin", ASK, {("seller", TILE): 0.0})
        return offers[0].reservation_price, result

    def test_the_ask_falls_to_what_a_buyer_pays_above_the_capitalised_rent_and_sells_out(self):
        ask, result = self.search(worth=2.0 * RENT / RATE)
        self.assertAlmostEqual(ask, 2.0 * RENT / RATE, delta=1e-3 * RENT / RATE)
        self.assertAlmostEqual(sum(fill.quantity for fill in result.fills if fill.side == "sell"), 800.0, delta=1e-3)

    def test_the_ask_stops_at_the_capitalised_rent_when_no_buyer_values_it_that_much(self):
        ask, _result = self.search(worth=0.5 * RENT / RATE)
        self.assertAlmostEqual(ask, RENT / RATE, delta=1e-3 * RENT / RATE)

    def test_the_stock_and_expected_sales_do_not_move_where_it_stops(self):
        self.assertAlmostEqual(self.search(2.0 * RENT / RATE, stock=10.0, expected_sales=5.0)[0],
                               self.search(2.0 * RENT / RATE, stock=3000.0, expected_sales=0.01)[0], places=3)


if __name__ == "__main__":
    unittest.main()
