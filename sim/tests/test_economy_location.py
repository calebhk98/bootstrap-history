"""Where a recipe is worked inside a market area: lowest expected cost among tiles with a site and spare hands."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import entry, location
from sim.economy.types import Recipe
from sim.tests import economy_fixture as fixture
from sim.tests.test_economy_producers import View


class SplitTests(unittest.TestCase):
    def test_split_follows_weights(self):
        self.assertEqual(location.split_runs(10.0, {"a": 1.0, "b": 3.0}, {}), {"a": 2.5, "b": 7.5})

    def test_a_capped_tile_hands_its_excess_to_the_others(self):
        self.assertEqual(location.split_runs(10.0, {"a": 1.0, "b": 1.0}, {"a": 2.0}), {"a": 2.0, "b": 8.0})

    def test_what_every_cap_cannot_take_is_dropped(self):
        self.assertEqual(location.split_runs(10.0, {"a": 1.0, "b": 1.0}, {"a": 2.0, "b": 3.0}), {"a": 2.0, "b": 3.0})

    def test_zero_weights_get_nothing(self):
        self.assertEqual(location.split_runs(10.0, {"a": 0.0, "b": 1.0}, {}), {"b": 10.0})


class CostTests(unittest.TestCase):
    recipe = Recipe("dig", {fixture.ORE: 1000.0}, {}, {"miner": 10.0})
    specs = fixture.specs()

    def test_wage_and_carriage_and_yield_make_the_cost(self):
        near = location.cost_per_run(self.recipe, {"miner": 1.0}, {}, 0.0, 0.0, 1.0)
        far = location.cost_per_run(self.recipe, {"miner": 1.0}, {}, 0.0, 2.0, 1.0, tonnes=1.0)
        poor = location.cost_per_run(self.recipe, {"miner": 1.0}, {}, 0.0, 0.0, 0.5)
        self.assertEqual((near, far, poor), (10.0, 12.0, 20.0))

    def test_rent_adds(self):
        self.assertEqual(location.cost_per_run(self.recipe, {"miner": 1.0}, {}, 3.0, 0.0, 1.0), 13.0)

    def test_carriage_is_for_the_output_mass(self):
        self.assertEqual(location.output_tonnes(self.recipe, self.specs), 1.0)

    def test_an_unpriced_trade_is_infinite(self):
        self.assertTrue(math.isinf(location.cost_per_run(self.recipe, {}, {}, 0.0, 0.0, 1.0)))


class ChooseTests(unittest.TestCase):
    def candidate(self, tile, cost, staffable=math.inf, headroom=math.inf):
        return location.Candidate(tile, cost, staffable, headroom)

    def test_the_cheapest_staffed_tile_wins(self):
        pick = location.choose([self.candidate("a", 5.0), self.candidate("b", 3.0)], 10.0)
        self.assertEqual((pick[0].tile, pick[1]), ("b", 10.0))

    def test_a_tile_that_cannot_staff_the_run_loses_to_one_that_can(self):
        pick = location.choose([self.candidate("a", 1.0, staffable=2.0), self.candidate("b", 3.0, staffable=20.0)], 10.0)
        self.assertEqual(pick[0].tile, "b")

    def test_when_none_can_the_run_shrinks_to_the_best_staffed(self):
        pick = location.choose([self.candidate("a", 1.0, staffable=2.0), self.candidate("b", 3.0, staffable=4.0)], 10.0)
        self.assertEqual((pick[0].tile, pick[1]), ("b", 4.0))

    def test_headroom_caps_the_run_and_none_means_none(self):
        pick = location.choose([self.candidate("a", 1.0, headroom=3.0)], 10.0)
        self.assertEqual(pick[1], 3.0)
        self.assertIsNone(location.choose([self.candidate("a", 1.0, headroom=0.0)], 10.0))
        self.assertIsNone(location.choose([], 10.0))

    def test_spare_hours_and_staffable_runs(self):
        self.assertEqual(location.spare_hours({"a": 2.0, "b": 1.0}, 100.0, 50.0), 250.0)
        recipe = Recipe("r", {"x": 1.0}, {}, {"a": 10.0, "b": 15.0})
        self.assertEqual(location.staffable_runs(recipe, 250.0), 10.0)
        self.assertTrue(math.isinf(location.staffable_runs(Recipe("r", {"x": 1.0}, {}, {}), 0.0)))


class EntrySitingTests(unittest.TestCase):
    salt = Recipe("boil_salt", {"salt": 10.0}, {}, {"hand": 2.0})
    unmet = {("salt", "area"): entry.UnmetDemand("salt", "area", "anchor", 100.0)}

    def plans(self, siting):
        view = View(prices={"salt": 1.0}, wages={"hand": 0.2})
        return entry.entry_plans({"boil_salt": self.salt}, view, self.unmet, siting=siting)

    def test_a_newcomer_goes_where_the_siting_says_with_the_runs_it_allows(self):
        chosen = self.plans(lambda recipe_id, demand, runs: ("far", runs / 2.0))
        self.assertEqual([(plan.tile, plan.runs) for plan in chosen], [("far", 2.5)])

    def test_no_tile_means_no_newcomer(self):
        self.assertEqual(self.plans(lambda recipe_id, demand, runs: None), [])

    def test_without_a_siting_the_anchor_is_kept(self):
        self.assertEqual([plan.tile for plan in self.plans(None)], ["anchor"])


class FixtureScenarioTests(unittest.TestCase):
    def test_the_opening_spreads_producers_over_the_tiles(self):
        economy, _outcomes = fixture.run(years=0)
        tiles = {producer.tile for producer in economy.record.producers.values() if producer.recipe_id == fixture.FARM}
        self.assertGreater(len(tiles), 1)

    def test_people_off_the_anchor_tile_find_work_and_food(self):
        # with every producer on the town tile, farms and hills households earned nothing and went hungry
        setup = fixture.small_setup()
        economy, outcomes = fixture.run(setup, years=10)
        floor = sum(setup.opening_population_by_tile[tile] for tile in (fixture.FARMS, fixture.HILLS)) * next(
            need.subsistence_per_person for need in setup.basket.needs if need.need_id == setup.hunger_need)
        hunger = sum(outcome.hunger_by_tile.get(tile, 0.0) for outcome in outcomes[1:]
                     for tile in (fixture.FARMS, fixture.HILLS))
        self.assertLess(hunger, 0.01 * floor * (len(outcomes) - 1))
        tiles = {producer.tile for producer in economy.record.producers.values()}
        self.assertIn(fixture.FARMS, tiles)
        self.assertEqual(economy.record.book.check_conservation(1e-6).breaches, ())


if __name__ == "__main__":
    unittest.main()
