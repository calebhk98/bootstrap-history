"""Complaint 473: land rent on a tile is shared among its uses by what a hectare is worth to each, so a use that earns
little a hectare (grain) is not charged the rent a use that earns a great deal a hectare (a mine) bids the tile up to."""

QUICK_TOPIC = True

import unittest

from sim.economy import land_market
from sim.economy.land_market import LandDemand, clear_land, rent_postings, use_rent_per_hectare
from sim.economy.types import EDGE_MINT, Recipe, Transfer
from sim.tests.test_economy_land_market import economy_of
from sim.tests.test_economy_producers import View

GRAIN_VALUE = 100.0         # output value per hectare of a low-value use
MINE_VALUE = 10000.0        # output value per hectare of a high-value use
SHORT_TILE = {"t": 100.0}   # land short enough that rent is positive


def two_uses(grain_hectares=90.0, mine_hectares=10.0):
    return [LandDemand("grain", "t", grain_hectares, GRAIN_VALUE, 40.0), LandDemand("mine", "t", mine_hectares, MINE_VALUE, 40.0)]


class UseRentTests(unittest.TestCase):
    def test_a_use_pays_the_tile_rent_in_proportion_to_its_value_a_hectare(self):
        demands = two_uses()
        result = clear_land({"t": 100.0}, demands)
        tile_rent = result.rent_per_hectare_by_tile["t"]
        grain = use_rent_per_hectare(result, "t", GRAIN_VALUE)
        mine = use_rent_per_hectare(result, "t", MINE_VALUE)
        self.assertGreater(tile_rent, 0.0)
        self.assertAlmostEqual(mine / grain, MINE_VALUE / GRAIN_VALUE)
        self.assertLess(grain, tile_rent)
        self.assertGreater(mine, tile_rent)

    def test_a_use_worth_the_tile_mean_pays_the_tile_rent(self):
        result = clear_land({"t": 100.0}, two_uses())
        mean_value = (90.0 * GRAIN_VALUE + 10.0 * MINE_VALUE) / 100.0
        self.assertAlmostEqual(use_rent_per_hectare(result, "t", mean_value), result.rent_per_hectare_by_tile["t"])

    def test_one_use_on_a_tile_pays_the_tile_rent(self):
        result = clear_land({"t": 50.0}, [two_uses()[0]])
        self.assertAlmostEqual(use_rent_per_hectare(result, "t", GRAIN_VALUE), result.rent_per_hectare_by_tile["t"])

    def test_the_rent_paid_in_all_is_the_tiles_rent_on_the_hectares_granted(self):
        demands = two_uses()
        result = clear_land({"t": 100.0}, demands)
        postings = rent_postings(result, demands, {"t": "owner"}, "coin")
        paid = {each.payer: each.amount for each in postings}
        self.assertAlmostEqual(sum(paid.values()), result.rent_per_hectare_by_tile["t"] * 100.0)
        self.assertAlmostEqual(paid["grain"], use_rent_per_hectare(result, "t", GRAIN_VALUE) * 90.0)
        self.assertGreater(paid["mine"] / 10.0, paid["grain"] / 90.0)

    def test_a_use_worth_nothing_a_hectare_pays_no_rent(self):
        result = clear_land({"t": 100.0}, two_uses())
        self.assertEqual(use_rent_per_hectare(result, "t", 0.0), 0.0)

    def test_a_tile_nobody_asked_land_on_charges_no_rent(self):
        result = clear_land({"t": 100.0}, [])
        self.assertEqual(use_rent_per_hectare(result, "t", GRAIN_VALUE), 0.0)


MINE = Recipe("mine", {"ore": 10.0}, {}, {"hand": 1.0})


class SettleYearByUseTests(unittest.TestCase):
    def build(self):
        setup, record = economy_of({"t": 100.0}, {"t": 300.0})
        setup.recipes["mine"] = MINE
        setup.land_per_run["mine"] = 1.0
        record.producers["producer:mine"] = record.producers["producer:t"].__class__(
            "producer:mine", record.producers["producer:t"].owner, "mine", "t", 300.0, expected_prices={"ore": 100.0})
        record.book.transfer(Transfer(EDGE_MINT, "producer:mine", "coin", 1e6, "opening"))
        return setup, record, View({"grain": 1.0, "ore": 100.0}, {"hand": 0.5})

    def test_an_idle_grain_producer_reads_rent_at_its_own_value_not_the_mines(self):
        setup, record, view = self.build()
        land_market.settle_year(setup, record, view, {"producer:mine": 300.0, "producer:t": 0.0})
        grain_rent = record.producers["producer:t"].land_rent_per_run
        mine_rent = record.producers["producer:mine"].land_rent_per_run
        self.assertGreater(mine_rent, 0.0)
        self.assertGreater(grain_rent, 0.0)
        self.assertAlmostEqual(mine_rent / grain_rent, 1000.0 / 100.0)       # ore 10 a run at 100, grain 100 a run at 1
        self.assertLess(grain_rent, record.land_rent["t"] * 1.0)

    def test_a_grain_producer_wanting_runs_pays_its_own_rate_on_what_it_is_granted(self):
        setup, record, view = self.build()
        wanted = {"producer:mine": 20.0, "producer:t": 80.0}
        paid = land_market.settle_year(setup, record, view, wanted)
        grain_rate = record.producers["producer:t"].land_rent_per_run
        mine_rate = record.producers["producer:mine"].land_rent_per_run
        self.assertGreater(mine_rate, grain_rate)
        self.assertAlmostEqual(sum(each.amount for each in paid), record.land_rent["t"] * 100.0)


if __name__ == "__main__":
    unittest.main()
