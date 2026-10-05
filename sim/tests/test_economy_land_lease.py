"""Rent flicker: the posted rent moves a share of the way to what the tile's land clears at."""
import unittest
from types import SimpleNamespace

from sim.economy import land_market
from sim.economy.accounts import Book
from sim.economy.households_cohort import cohort_id, cohorts_for_tile
from sim.economy.producers import Producer
from sim.economy.types import EDGE_MINT, Recipe, TileSpec, Transfer
from sim.tests.test_economy_producers import View

WHEAT = Recipe("wheat", {"grain": 100.0}, {}, {"hand": 10.0})


def economy_with(hectares):
    tiles = {"t": TileSpec("t", 40.0, 0.0, hectares / 100.0, False, (), 1.0, 1.0)}
    cohorts = list(cohorts_for_tile("t", 3000.0, 0.5, 0.4))
    book = Book()
    producer = Producer("producer:t", cohort_id("t", 2), "wheat", "t", 100.0, expected_prices={"grain": 1.0})
    book.transfer(Transfer(EDGE_MINT, "producer:t", "coin", 1e9, "opening"))
    record = SimpleNamespace(producers={"producer:t": producer}, book=book,
                             cohorts={each.agent_id: each for each in cohorts}, land_rent={})
    setup = SimpleNamespace(tiles=tiles, recipes={"wheat": WHEAT}, land_per_run={"wheat": 1.0}, currency_id="coin")
    return setup, record


def view():
    return View({"grain": 1.0}, {"hand": 0.5})


def cleared_rent(setup, record, runs):
    demands = land_market.demands_of(setup, record, view(), {"producer:t": runs})
    return land_market.clear_land({"t": 100.0}, demands).rent_per_hectare_by_tile["t"]


def settle(setup, record, runs):
    land_market.settle_year(setup, record, view(), {"producer:t": runs})
    return record.land_rent["t"]


class LeaseTests(unittest.TestCase):
    def test_the_first_posting_is_what_the_land_clears_at(self):
        setup, record = economy_with(100.0)
        self.assertAlmostEqual(settle(setup, record, 300.0), cleared_rent(setup, record, 300.0))

    def test_rent_moves_only_a_share_of_the_way_when_demand_changes(self):
        setup, record = economy_with(100.0)
        high = settle(setup, record, 300.0)
        low_cleared = cleared_rent(setup, record, 5.0)        # within the best band: no rent
        self.assertAlmostEqual(low_cleared, 0.0)
        posted = settle(setup, record, 5.0)
        self.assertGreater(posted, low_cleared)
        self.assertLess(posted, high)
        self.assertAlmostEqual(posted, high + land_market.LAND_RENT_ADJUSTMENT_SHARE * (low_cleared - high))

    def test_a_tile_nobody_asks_land_on_decays_instead_of_dropping_to_zero(self):
        setup, record = economy_with(100.0)
        high = settle(setup, record, 300.0)
        land_market.settle_year(setup, record, view(), {})
        self.assertAlmostEqual(record.land_rent["t"], high * (1.0 - land_market.LAND_RENT_ADJUSTMENT_SHARE))

    def test_alternating_demand_swings_rent_less_than_it_swings_what_land_clears_at(self):
        setup, record = economy_with(100.0)
        series = [settle(setup, record, runs) for runs in (300.0, 5.0) * 6]
        late = series[4:]
        cleared = [cleared_rent(setup, record, runs) for runs in (300.0, 5.0)]
        self.assertLess(max(late) - min(late), 0.7 * (max(cleared) - min(cleared)))

    def test_producers_plan_with_and_pay_the_posted_rent(self):
        setup, record = economy_with(100.0)
        settle(setup, record, 300.0)
        before = record.book.balance("producer:t", "coin")
        paid = land_market.settle_year(setup, record, view(), {"producer:t": 5.0})
        self.assertAlmostEqual(record.producers["producer:t"].land_rent_per_run, record.land_rent["t"])
        self.assertAlmostEqual(sum(each.amount for each in paid), before - record.book.balance("producer:t", "coin"))
        self.assertGreater(sum(each.amount for each in paid), 0.0)


if __name__ == "__main__":
    unittest.main()
