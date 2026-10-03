"""The land market: arable hectares in quality bands, producers' and households' demand, differential
rent, rationing when land is short, and rent paid to the tile's owners."""
import math
import unittest
from types import SimpleNamespace

from sim.economy import land_market
from sim.economy.accounts import Book
from sim.economy.households_cohort import cohort_id, cohorts_for_tile
from sim.economy.land_market import LandDemand, clear_land, rent_postings
from sim.economy.producers import Producer
from sim.economy.types import EDGE_MINT, Recipe, TileSpec, Transfer
from sim.tests.test_economy_producers import View

VALUE = 100.0       # output value per hectare at average fertility
COST = 40.0         # other cost per hectare


def demand(agent="p1", tile="t", hectares=10.0):
    return LandDemand(agent, tile, hectares, VALUE, COST)


def band_spread():
    shares, fertilities = land_market.LAND_BAND_AREA_SHARES, land_market.LAND_BAND_RELATIVE_FERTILITY
    return shares, fertilities


class BandTests(unittest.TestCase):
    def test_the_bands_cover_the_arable_area_and_average_to_the_tiles_fertility(self):
        shares, fertilities = band_spread()
        self.assertAlmostEqual(sum(shares), 1.0)
        self.assertAlmostEqual(sum(share * fertility for share, fertility in zip(shares, fertilities)), 1.0)


class ClearLandTests(unittest.TestCase):
    def test_a_land_rich_tile_charges_nothing_and_grants_everything(self):
        result = clear_land({"t": 1000.0}, [demand(hectares=20.0)])
        self.assertEqual(result.granted_hectares["p1"], 20.0)
        self.assertAlmostEqual(result.rent_per_hectare_by_tile["t"], 0.0)

    def test_demand_spilling_into_a_worse_band_pays_the_differential(self):
        shares, fertilities = band_spread()
        best_band = 100.0 * shares[0]
        wanted = best_band + 10.0              # ten hectares into the second band
        result = clear_land({"t": 100.0}, [demand(hectares=wanted)])
        self.assertEqual(result.granted_hectares["p1"], wanted)
        extra = VALUE * (fertilities[0] - fertilities[1])
        self.assertAlmostEqual(result.rent_per_hectare_by_tile["t"], best_band * extra / wanted)

    def test_a_land_short_tile_charges_scarcity_rent_and_grants_a_share(self):
        shares, fertilities = band_spread()
        result = clear_land({"t": 100.0}, [demand(hectares=300.0)])
        self.assertAlmostEqual(result.granted_hectares["p1"], 100.0)
        differential = sum(100.0 * share * VALUE * (fertility - fertilities[-1])
                           for share, fertility in zip(shares, fertilities)) / 100.0
        scarcity = land_market.LAND_SCARCITY_RENT_SHARE * (VALUE * fertilities[-1] - COST)
        self.assertAlmostEqual(result.rent_per_hectare_by_tile["t"], differential + scarcity)

    def test_the_grant_is_shared_in_proportion_to_demand(self):
        result = clear_land({"t": 100.0}, [demand("a", hectares=100.0), demand("b", hectares=300.0)])
        self.assertAlmostEqual(result.granted_hectares["a"], 25.0)
        self.assertAlmostEqual(result.granted_hectares["b"], 75.0)

    def test_households_own_plots_take_land_first(self):
        result = clear_land({"t": 100.0}, [demand(hectares=100.0)], {"t": 60.0})
        self.assertAlmostEqual(result.granted_hectares["p1"], 40.0)

    def test_rent_rises_as_land_gets_scarcer(self):
        rents = [clear_land({"t": 100.0}, [demand(hectares=wanted)]).rent_per_hectare_by_tile["t"]
                 for wanted in (20.0, 60.0, 100.0, 200.0, 400.0)]
        self.assertEqual(rents, sorted(rents))
        self.assertGreater(rents[-1], rents[0])

    def test_a_tile_with_no_arable_land_grants_nothing(self):
        result = clear_land({"t": 0.0}, [demand(hectares=5.0)])
        self.assertEqual(result.granted_hectares["p1"], 0.0)

    def test_tiles_are_cleared_separately(self):
        result = clear_land({"t": 1000.0, "u": 10.0}, [demand("a", "t", 50.0), demand("b", "u", 50.0)])
        self.assertAlmostEqual(result.rent_per_hectare_by_tile["t"], 0.0)
        self.assertGreater(result.rent_per_hectare_by_tile["u"], 0.0)
        self.assertEqual(result.granted_hectares["a"], 50.0)
        self.assertAlmostEqual(result.granted_hectares["b"], 10.0)


class PostingTests(unittest.TestCase):
    def test_producers_pay_rent_per_hectare_granted_to_the_tiles_owner(self):
        result = clear_land({"u": 10.0}, [demand("b", "u", 50.0)])
        owed = result.rent_per_hectare_by_tile["u"] * 10.0
        postings = rent_postings(result, [demand("b", "u", 50.0)], {"u": "owner"}, "coin")
        self.assertEqual([(each.payer, each.payee, each.purpose) for each in postings], [("b", "owner", "rent")])
        self.assertAlmostEqual(postings[0].amount, owed)

    def test_a_producer_pays_no_more_than_it_holds(self):
        demands = [demand("b", "u", 50.0)]
        result = clear_land({"u": 10.0}, demands)
        postings = rent_postings(result, demands, {"u": "owner"}, "coin", {"b": 1.0})
        self.assertAlmostEqual(postings[0].amount, 1.0)

    def test_no_rent_no_posting(self):
        demands = [demand(hectares=5.0)]
        self.assertEqual(rent_postings(clear_land({"t": 1000.0}, demands), demands, {"t": "owner"}, "coin"), [])


# ---- the year's settlement on a book -----------------------------------------------------------

WHEAT = Recipe("wheat", {"grain": 100.0}, {}, {"hand": 10.0})
LAND_PER_RUN = {"wheat": 1.0}


def economy_of(arable_by_tile, runs_by_tile):
    """A record with one grain producer per tile, each holding cash, and three cohorts per tile."""
    tiles = {tile: TileSpec(tile, 40.0, 0.0, hectares / 100.0, False, (), 1.0, 1.0)
             for tile, hectares in arable_by_tile.items()}
    cohorts = [cohort for tile in tiles for cohort in cohorts_for_tile(tile, 3000.0, 0.5, 0.4)]
    book = Book()
    producers = {}
    for tile in tiles:
        producer_id = "producer:" + tile
        producers[producer_id] = Producer(producer_id, cohort_id(tile, 2), "wheat", tile, runs_by_tile[tile],
                                          expected_prices={"grain": 1.0})
        book.transfer(Transfer(EDGE_MINT, producer_id, "coin", 1e6, "opening"))
    record = SimpleNamespace(producers=producers, book=book, cohorts={each.agent_id: each for each in cohorts},
                             land_rent={})
    setup = SimpleNamespace(tiles=tiles, recipes={"wheat": WHEAT}, land_per_run=LAND_PER_RUN, currency_id="coin")
    return setup, record


class SettleYearTests(unittest.TestCase):
    def test_a_land_short_tile_charges_rent_and_caps_runs_while_a_land_rich_tile_does_not(self):
        setup, record = economy_of({"rich": 10000.0, "short": 100.0}, {"rich": 100.0, "short": 300.0})
        view = View({"grain": 1.0}, {"hand": 0.5})
        wanted = {pid: producer.capacity_runs for pid, producer in record.producers.items()}
        paid = land_market.settle_year(setup, record, view, wanted)
        self.assertAlmostEqual(record.land_rent["rich"], 0.0)
        self.assertGreater(record.land_rent["short"], 0.0)
        self.assertEqual(record.producers["producer:rich"].land_run_cap, -1.0)
        self.assertAlmostEqual(record.producers["producer:short"].land_run_cap, 100.0)
        self.assertAlmostEqual(record.producers["producer:short"].land_rent_per_run, record.land_rent["short"])
        self.assertAlmostEqual(sum(each.amount for each in paid), 100.0 * record.land_rent["short"])
        # the rent reaches every cohort of the short tile by ownership share, none of the rich tile's
        self.assertEqual({each.payee.split(":")[1] for each in paid}, {"short"})
        self.assertEqual(len({each.payee for each in paid}), 3)
        self.assertAlmostEqual(record.book.balance("producer:short", "coin"), 1e6 - sum(each.amount for each in paid))

    def test_the_cap_does_not_shrink_what_the_producer_wants_next_year(self):
        setup, record = economy_of({"short": 100.0}, {"short": 300.0})
        view = View({"grain": 1.0}, {"hand": 0.5})
        for _year in range(3):
            land_market.settle_year(setup, record, view, {"producer:short": 300.0})
        self.assertAlmostEqual(record.producers["producer:short"].land_run_cap, 100.0)

    def test_rent_stays_zero_until_settled(self):
        setup, record = economy_of({"short": 100.0}, {"short": 300.0})
        self.assertEqual(record.land_rent, {})
        self.assertEqual(record.producers["producer:short"].land_rent_per_run, 0.0)
        self.assertTrue(math.isfinite(record.producers["producer:short"].capacity_runs))


if __name__ == "__main__":
    unittest.main()
