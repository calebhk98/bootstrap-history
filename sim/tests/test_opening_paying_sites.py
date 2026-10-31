"""The opening places a producer only where its run pays at the opening's prices and wages (the test `producers.plan`
applies in year 1), and sizes its plant so that the year-1 plan is what the opening expects it to sell. Each rule is
one plain function over written-out inputs."""

QUICK_TOPIC = True

import unittest

from sim.economy import crop_sites, opening_income, producers
from sim.economy.types import Recipe

FARM = Recipe("farm", outputs={"grain": 100.0}, inputs={}, labour_hours={"farmer": 10.0})
PRICES = {"grain": 1.0}
WAGES = {"farmer": 1.0}


class LowestPayingYieldTests(unittest.TestCase):
    def test_a_run_pays_from_the_yield_at_which_revenue_equals_variable_cost(self):
        self.assertAlmostEqual(crop_sites.lowest_paying_yield(FARM, PRICES, WAGES), 0.1)

    def test_a_run_whose_cost_cannot_be_priced_has_no_floor(self):
        self.assertEqual(crop_sites.lowest_paying_yield(FARM, PRICES, {}), 0.0)


class PaysTests(unittest.TestCase):
    def test_a_tile_whose_run_earns_less_than_it_costs_is_not_a_place_to_put_a_producer(self):
        self.assertFalse(crop_sites.pays(FARM, 0.05, PRICES, WAGES))

    def test_a_tile_whose_run_covers_its_cost_is(self):
        self.assertTrue(crop_sites.pays(FARM, 0.2, PRICES, WAGES))

    def test_a_tile_that_grows_nothing_is_not(self):
        self.assertFalse(crop_sites.pays(FARM, 0.0, PRICES, {}))


class PaysAtCostTests(unittest.TestCase):
    def test_a_run_priced_at_its_cost_pays_whatever_the_last_digit_of_the_sum(self):
        at_cost = Recipe("at_cost", outputs={"good": 1.0}, inputs={}, labour_hours={"hand": 3.0})
        self.assertTrue(crop_sites.pays(at_cost, 1.0, {"good": 0.3}, {"hand": 0.1}))     # 3 * 0.1 is 0.30000000000000004


class SitesTests(unittest.TestCase):
    def test_the_paying_tiles_are_kept_and_the_poorer_ones_dropped(self):
        self.assertEqual(crop_sites.sites({"a": 0.05, "b": 0.5}, FARM, PRICES, WAGES), ["b"])

    def test_where_no_tile_pays_the_tiles_that_grow_anything_are_kept(self):
        self.assertEqual(crop_sites.sites({"a": 0.05, "b": 0.02, "c": 0.0}, FARM, PRICES, WAGES), ["a", "b"])

    def test_no_tile_that_grows_anything_gives_none(self):
        self.assertEqual(crop_sites.sites({"c": 0.0}, FARM, PRICES, WAGES), [])


class PayingSetTests(unittest.TestCase):
    def test_tiles_below_the_floor_are_left_out(self):
        self.assertEqual(crop_sites.paying({"a": 0.05, "b": 0.1, "c": 0.9}, 0.1), ["b", "c"])


class SupplyYieldTests(unittest.TestCase):
    def test_tiles_that_do_not_cover_variable_cost_at_the_price_the_rest_set_are_dropped(self):
        # the best tiles' harmonic mean sets a price; a tile under variable_share of it cannot pay at that price
        people = {"a": 1.0, "b": 1.0, "c": 1.0}
        yields = {"a": 1.0, "b": 0.5, "c": 0.01}
        supply = crop_sites.supply_yield(people, yields, variable_share=0.5)
        self.assertAlmostEqual(supply, 2.0 / (1.0 / 1.0 + 1.0 / 0.5))

    def test_no_tile_that_grows_anything_gives_none(self):
        self.assertIsNone(crop_sites.supply_yield({"a": 1.0}, {"a": 0.0}, variable_share=0.5))


class WorkingShareAtYieldTests(unittest.TestCase):
    def test_a_run_that_earns_next_to_nothing_still_has_a_plant_to_size(self):
        self.assertGreater(opening_income.working_share(FARM, PRICES, WAGES, 1e-300), 0.0)

    def test_the_plant_is_sized_so_the_year_one_plan_is_the_expected_sales(self):
        factor = 0.12      # a run earns 12 against a cost of 10 at this tile's yield
        share = opening_income.working_share(FARM, PRICES, WAGES, factor)
        self.assertAlmostEqual(share, producers.share_working(100.0 * factor, 10.0))
        self.assertLess(share, 1.0)


if __name__ == "__main__":
    unittest.main()
