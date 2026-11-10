"""Rules that read the cohorts without building a `Cohort` (`cohort_reads.py`, `land_lease_year._margins`, `capital_year.note_exposure`,
`carriage_hours.bids`, `merchants_dispatch`'s carrier choice, `land_bid_year.best_margin`) give what the loops over `Cohort` objects gave,
on written-out cohorts held as a column store and as a plain mapping."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import capital_year, carriage_hours, land_bid_year, land_lease_year
from sim.economy.cohort_reads import (figures_in_id_order, figures_of, poorest_by_tile, populated_tiles, tile_of, tiles_by_first_id)
from sim.economy.cohort_store import CohortStore
from sim.economy.households_cohort import Cohort
from sim.economy.insurance import HARVEST, RISK_POOLING
from sim.economy.market_memory import market_key
from sim.economy.merchants import Merchant
from sim.tests import economy_fixture as fixture
from sim.tests.test_economy_carriage_hours import trading_setup
from sim.tests.test_economy_land_lease_year import POOR, TILE, View, world


def _cohorts():
    """Entered in this order: b before a, two tiles, a tie for the poorest class on tile:x."""
    return [Cohort("household:x:b", "tile:x", 1, 30.0, 12.0, 0.6, last_year_income=5.0),
            Cohort("household:y:c", "tile:y", 0, 10.0, 4.0, 0.4, last_year_income=2.0),
            Cohort("household:x:a", "tile:x", 1, 20.0, 8.0, 0.5, last_year_income=3.0),
            Cohort("household:x:z", "tile:x", 2, 5.0, 2.0, 0.1, last_year_income=1.0)]


def _both():
    cohorts = _cohorts()
    return CohortStore({each.agent_id: each for each in cohorts}), {each.agent_id: each for each in cohorts}


class ReadsMatchTheObjects(unittest.TestCase):
    def test_populated_tiles(self):
        store, plain = _both()
        self.assertEqual(populated_tiles(store), {"tile:x", "tile:y"})
        self.assertEqual(populated_tiles(store), populated_tiles(plain))

    def test_tile_of_an_id_and_none_for_a_stranger(self):
        store, plain = _both()
        for mapping in (store, plain):
            self.assertEqual(tile_of(mapping, "household:y:c"), "tile:y")
            self.assertIsNone(tile_of(mapping, "household:nobody"))

    def test_the_poorest_of_a_tile_is_the_first_in_table_order_among_the_lowest_class(self):
        store, plain = _both()
        found = poorest_by_tile(store)
        self.assertEqual(found, {"tile:x": "household:x:b", "tile:y": "household:y:c"})     # b entered before a: both are class 1 but z is 2
        self.assertEqual(list(found.items()), list(poorest_by_tile(plain).items()))

    def test_the_poorest_tie_goes_to_the_first_entered_not_the_lowest_id(self):
        cohorts = [Cohort("household:x:b", "tile:x", 0, 1.0, 1.0, 0.5), Cohort("household:x:a", "tile:x", 0, 1.0, 1.0, 0.5)]
        store = CohortStore({each.agent_id: each for each in cohorts})
        self.assertEqual(poorest_by_tile(store), {"tile:x": "household:x:b"})
        self.assertEqual(poorest_by_tile(store), poorest_by_tile({each.agent_id: each for each in cohorts}))

    def test_tiles_by_first_id_follow_the_ids_not_the_table(self):
        store, plain = _both()
        self.assertEqual(tiles_by_first_id(store), ["tile:x", "tile:y"])      # household:x:a sorts before household:y:c
        self.assertEqual(tiles_by_first_id(store), tiles_by_first_id(plain))

    def test_figures_in_id_order_are_the_fields_of_the_cohorts_in_id_order(self):
        store, plain = _both()
        wanted = [(each.agent_id, each.tile, each.people, each.working_people, each.last_year_income)
                  for each in sorted(_cohorts(), key=lambda each: each.agent_id)]
        for mapping in (store, plain):
            self.assertEqual([(each.agent_id, each.tile, each.people, each.working_people, each.last_year_income)
                              for each in figures_in_id_order(mapping)], wanted)

    def test_figures_of_one_cohort_and_none_for_a_stranger(self):
        store, _plain = _both()
        found = figures_of(store, "household:x:a")
        self.assertEqual((found.agent_id, found.tile, found.people, found.working_people), ("household:x:a", "tile:x", 20.0, 8.0))
        self.assertIsNone(figures_of(store, "household:nobody"))

    def test_no_cohort_is_built_by_these_reads(self):
        store, _plain = _both()
        store.written()
        populated_tiles(store), poorest_by_tile(store), tiles_by_first_id(store), figures_in_id_order(store), figures_of(store, "household:x:a")
        tile_of(store, "household:x:a")
        self.assertTrue(all(kept is None for kept in store._objects))


class LeaseMargins(unittest.TestCase):
    def _two_tile_world(self):
        setup, record, options = world()
        second = types.SimpleNamespace(**vars(setup.tiles[TILE]))
        setup.tiles = {TILE: setup.tiles[TILE], "u": second}
        record.cohorts = CohortStore({each.agent_id: each for each in (
            Cohort("household:u:0", "u", 0, 10.0, 10.0, 0.0), Cohort(POOR, TILE, 0, 10.0, 10.0, 0.0), Cohort("household:u:1", "u", 0, 4.0, 4.0, 0.0),
            Cohort("household:nowhere:0", "nowhere", 0, 4.0, 4.0, 0.0))})      # a tile the setup does not know is left out
        return setup, record, options

    def test_margins_are_the_object_loop_s_in_values_and_order(self):
        setup, record, options = self._two_tile_world()
        view = View(0.2, tools=100.0)
        expected = {}
        for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
            tile = setup.tiles.get(cohort.tile)
            if tile is not None and cohort.tile not in expected:
                margin, _hours, recipe_id = land_bid_year.best_margin(setup, view, cohort.tile, options, tile)
                expected[cohort.tile] = (margin, recipe_id)
        record.cohorts.written()
        found = land_lease_year._margins(setup, record, view, options)
        self.assertEqual(list(found.items()), list(expected.items()))
        self.assertEqual(list(found), [TILE, "u"])     # household:t:0 sorts before household:u:0
        self.assertTrue(all(kept is None for kept in record.cohorts._objects))

    def test_the_margin_depends_on_the_tile_id_alone(self):
        setup, record, options = world()
        view = View(0.2, tools=100.0)
        cohort = record.cohorts[POOR]
        self.assertEqual(land_bid_year.best_margin(setup, view, TILE, options, setup.tiles[TILE]),
                         land_bid_year.best_margin(setup, view, cohort.tile, options, setup.tiles[cohort.tile]))
        self.assertGreater(land_bid_year.best_margin(setup, view, TILE, options, setup.tiles[TILE])[0], 0.0)

    def test_the_lease_is_the_same_from_a_store_and_a_plain_mapping_and_builds_no_cohort(self):
        setup, record, options = world()
        plain_leases = land_lease_year.lease_in_market(setup, record, View(0.2, tools=100.0), options)
        setup, record, options = world()
        record.cohorts = CohortStore(record.cohorts)
        record.cohorts.written()
        leases = land_lease_year.lease_in_market(setup, record, View(0.2, tools=100.0), options)
        self.assertEqual(leases, plain_leases)
        self.assertTrue(all(kept is None for kept in record.cohorts._objects))

    def test_own_hectares_are_the_same_from_a_cohort_and_its_figures(self):
        setup, record, options = world()
        cohort = record.cohorts[POOR]
        tools = lambda _cohort, _recipe: {"hoe": 100.0}          # noqa: E731
        by_object = land_lease_year._own_hectares(setup, record, cohort, setup.tiles[TILE], options, "grow_grain", tools)
        by_figures = land_lease_year._own_hectares(setup, record, figures_of(CohortStore({POOR: cohort}), POOR), setup.tiles[TILE], options,
                                                   "grow_grain", tools)
        self.assertEqual(by_object, by_figures)


class ExposureOfTheHarvest(unittest.TestCase):
    def _run(self, cohorts):
        state = types.SimpleNamespace(exposure={})
        record = types.SimpleNamespace(cohorts=cohorts, capital_markets=types.SimpleNamespace(capital=state))
        asked = []

        class Prices:
            def price(self, good, area):
                return {"grain": 2.0, "salt": None}[good]

        class Areas:
            def area_of(self, good, tile):
                asked.append((good, tile))
                return tile

        ledger = types.SimpleNamespace(grown={"household:x:a": {"grain": 6.0, "salt": 3.0}, "household:y:c": {"salt": 1.0},
                                             "household:nobody": {"grain": 9.0}})
        capital_year.note_exposure(None, record, Prices(), Areas(), ledger, 0.5, (RISK_POOLING,))
        return state.exposure, asked

    def test_a_household_s_plot_yield_over_the_weather_at_its_tile_s_price(self):
        store, plain = _both()
        store.written()
        exposed, asked = self._run(store)
        self.assertEqual(exposed, {"household:x:a": {HARVEST: 24.0}})      # 6 grain at 2.0 over a harvest factor of 0.5; salt is unpriced
        self.assertIn(("grain", "tile:x"), asked)
        self.assertTrue(all(kept is None for kept in store._objects))
        self.assertEqual(self._run(plain)[0], exposed)


class CarriersAreBidForWhereThePeopleAre(unittest.TestCase):
    def _bids(self, cohorts):
        who = Merchant("m1", "town", "owner", 1.0)
        who.carriage_hours_wanted = {market_key(fixture.LABOURER, "hills"): 40.0, market_key(fixture.LABOURER, "farms"): 10.0}
        record = types.SimpleNamespace(merchants={"m1": who}, cohorts=cohorts, area_imbalance=1.0)
        return carriage_hours.bid_figures(trading_setup(), record), record

    def test_a_store_and_a_plain_mapping_give_the_same_bids_and_no_cohort_is_built(self):
        tiles = ("farms", "town")
        store = CohortStore({each: Cohort(each, tile, 0, 1.0, 1.0, 0.0) for each, tile in (("c:farms", "farms"), ("c:town", "town"))})
        plain = {each: types.SimpleNamespace(tile=tile) for each, tile in (("c:farms", "farms"), ("c:town", "town"))}
        store.written()
        by_store, record = self._bids(store)
        self.assertEqual(by_store, self._bids(plain)[0])
        self.assertEqual(sorted(figure[2] for figure in by_store), ["work@farms", "work@town"])      # the hills have nobody: hired at home
        self.assertEqual(populated_tiles(record.cohorts), set(tiles))
        self.assertTrue(all(kept is None for kept in store._objects))


if __name__ == "__main__":
    unittest.main()
