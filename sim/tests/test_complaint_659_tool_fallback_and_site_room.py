"""Complaint 659: a short tool never stops a run (the next tool in the trade's basket is drawn, then the work is
done by hand), an opening does not carry a tool shortage through every user, a sited good's second share on a
tile adds to the producer, and a deposit's yearly room follows the rate the data say it was worked at.
Each test calls the rule on built inputs."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import opening, opening_runs, tool_fallback
from sim.economy.producers import Producer, produce
from sim.economy.record import EconomyRecord
from sim.economy.tool_wear import with_tool_wear
from sim.economy.types import Recipe, SiteLimit, ToolFallback
from sim.markets.port_setup import tool_wear_recipes
from sim.resources import rules
from sim.world import deposits as deposit_model

HOURS_PER_YEAR = 2000.0
REGISTRY = {"hand": {"tool_basket": ["iron", "wood"], "tool_stock_per_worker": {"iron": 1.0, "wood": 2.0},
                     "tool_hours_factor": {"wood": 1.5}, "tool_hours_factor_by_hand": 2.5}}
LIVES = {"iron": 4.0, "wood": 2.0}
MAKERS = {"iron": Recipe("iron", {"iron": 1.0}, {}, {"smith": 1.0}), "wood": Recipe("wood", {"wood": 1.0}, {}, {"carpenter": 1.0})}


def farm(workers=1.0):
    return Recipe("farm", {"grain": 10.0}, {"seed": 1.0}, {"hand": workers * HOURS_PER_YEAR})


def worn_farm(workers=1.0):
    return tool_wear_recipes({"farm": farm(workers), **MAKERS}, REGISTRY, LIVES, HOURS_PER_YEAR)["farm"]


class BasketOrderTests(unittest.TestCase):
    def test_the_first_tool_is_worn_and_the_later_ones_and_working_by_hand_are_its_fallbacks(self):
        worn = worn_farm()
        self.assertEqual(set(worn.tool_wear), {"iron"})
        self.assertAlmostEqual(worn.tool_wear["iron"], 1.0 / 4.0)
        wood, by_hand = worn.tool_fallbacks["iron"]
        self.assertEqual((wood.good, wood.hours_factor), ("wood", 1.5))
        self.assertAlmostEqual(wood.units_per_run, 2.0 / 2.0)
        self.assertEqual((by_hand.good, by_hand.units_per_run, by_hand.hours_factor), ("", 0.0, 2.5))

    def test_a_tool_nothing_makes_is_skipped_for_the_next_in_the_basket(self):
        recipes = tool_wear_recipes({"farm": farm(), "wood": MAKERS["wood"]}, REGISTRY, LIVES, HOURS_PER_YEAR)
        self.assertEqual(set(recipes["farm"].tool_wear), {"wood"})

    def test_hard_inputs_leave_out_the_tools(self):
        self.assertEqual(worn_farm().hard_inputs, {"seed": 1.0})


class ShortToolTests(unittest.TestCase):
    def setUp(self):
        self.recipe = worn_farm()
        self.producer = Producer("p", "owner", "farm", "tile", capacity_runs=1.0)
        self.hours = {"hand": HOURS_PER_YEAR}

    def run_with(self, held, hours=None):
        return produce(self.producer, self.recipe, {"seed": 1.0, **held}, hours or self.hours, 1.0)

    def used(self, moves):
        return {move.good: move.quantity for move in moves if move.purpose == "input"}

    def test_with_iron_tools_in_hand_the_run_is_whole_and_draws_only_iron(self):
        runs, moves = self.run_with({"iron": 1.0, "wood": 5.0})
        self.assertAlmostEqual(runs, 1.0)
        self.assertEqual(set(self.used(moves)), {"seed", "iron"})

    def test_a_recipe_whose_iron_tools_are_short_draws_wooden_tools_and_still_runs(self):
        hours = {"hand": HOURS_PER_YEAR * 1.5}
        runs, moves = self.run_with({"iron": 0.0, "wood": 5.0}, hours)
        self.assertAlmostEqual(runs, 1.0)
        used = self.used(moves)
        self.assertNotIn("iron", used)
        self.assertAlmostEqual(used["wood"], self.recipe.tool_fallbacks["iron"][0].units_per_run)

    def test_wooden_tools_ask_more_hours_so_hired_hours_set_the_runs(self):
        runs, _moves = self.run_with({"wood": 5.0})
        self.assertAlmostEqual(runs, 1.0 / 1.5)

    def test_with_no_tool_at_all_the_work_is_done_by_hand_in_more_hours(self):
        runs, moves = self.run_with({})
        self.assertAlmostEqual(runs, 1.0 / 2.5)
        self.assertEqual(set(self.used(moves)), {"seed"})

    def test_part_of_the_iron_covers_part_of_the_runs(self):
        recipe = worn_farm()
        producer = Producer("p", "owner", "farm", "tile", capacity_runs=4.0)
        wear = recipe.tool_wear["iron"]
        used, extra = tool_fallback.draws(recipe, {"iron": 2.0 * wear, "wood": 9.0}, 4.0)
        self.assertAlmostEqual(used["iron"], 2.0 * wear)
        self.assertAlmostEqual(used["wood"], 2.0 * recipe.tool_fallbacks["iron"][0].units_per_run)
        self.assertAlmostEqual(extra["hand"], 2.0 * 0.5 * HOURS_PER_YEAR)
        self.assertEqual(producer.capacity_runs, 4.0)

    def test_a_missing_hard_input_still_stops_the_run(self):
        runs, _moves = produce(self.producer, self.recipe, {"iron": 1.0}, self.hours, 1.0)
        self.assertEqual(runs, 0.0)

    def test_a_recipe_without_fallbacks_is_not_stopped_by_its_tool_either(self):
        recipe = with_tool_wear(farm(), {"hand": {"iron": 1.25e-4}}, ["iron"])
        runs, _moves = produce(self.producer, recipe, {"seed": 1.0}, self.hours, 1.0)
        self.assertAlmostEqual(runs, 1.0)


class OpeningToolShortageTests(unittest.TestCase):
    """A deposit-bound ore feeds a tool maker; a farm wears the tool and eats the grain a baker needs."""

    def setUp(self):
        self.recipes = {
            "dig": Recipe("dig", {"ore": 1.0}, {}, {"labourer": 1.0}, site_bound=True),
            "forge": Recipe("forge", {"tool": 1.0}, {"ore": 1.0}, {"smith": 1.0}),
            "farm": Recipe("farm", {"grain": 10.0}, {"tool": 1.0}, {"farmer": 1.0}, tool_wear={"tool": 1.0},
                           tool_fallbacks={"tool": (ToolFallback("", 0.0, 2.0, ("farmer",)),)}),
            "bake": Recipe("bake", {"bread": 1.0}, {"grain": 1.0}, {"baker": 1.0}),
        }
        self.setup = types.SimpleNamespace(recipes=self.recipes, site_limits=(SiteLimit("dig", "tile", 10.0),))
        self.record = EconomyRecord.__new__(EconomyRecord)
        self.record.producers = {
            "dig": Producer("dig", "o", "dig", "tile", 10.0, expected_sales=10.0),
            "forge": Producer("forge", "o", "forge", "tile", 100.0, expected_sales=100.0),
            "farm": Producer("farm", "o", "farm", "tile", 100.0, expected_sales=100.0),
            "bake": Producer("bake", "o", "bake", "tile", 1000.0, expected_sales=1000.0),
        }

    def test_fit_to_supply_does_not_pass_a_tool_shortage_through_every_user(self):
        opening_runs.fit_to_supply(self.setup, self.record)
        self.assertAlmostEqual(self.record.producers["forge"].expected_sales, 10.0)
        self.assertAlmostEqual(self.record.producers["farm"].expected_sales, 100.0)
        self.assertAlmostEqual(self.record.producers["bake"].expected_sales, 1000.0)

    def test_goods_made_with_a_tool_are_not_bound_by_the_deposit_that_limits_the_tool(self):
        limited = opening_runs.limited_goods(self.recipes, {"dig": {"tile": object()}})
        self.assertIn("tool", limited)
        self.assertNotIn("grain", limited)

    def test_a_ceiling_on_a_tool_does_not_cap_the_runs_that_wear_it(self):
        ceilings = opening_runs.run_ceilings(self.recipes, {"dig": {"tile": SiteLimit("dig", "tile", 10.0)}})
        self.assertAlmostEqual(ceilings["forge"], 10.0)
        self.assertNotIn("farm", ceilings)

    def test_the_wear_a_capped_tool_cannot_meet_moves_to_the_next_tool(self):
        recipes = dict(self.recipes)
        recipes["farm"] = Recipe("farm", {"grain": 10.0}, {"tool": 1.0}, {"farmer": 1.0}, tool_wear={"tool": 1.0},
                                 tool_fallbacks={"tool": (ToolFallback("plank", 3.0, 1.5, ("farmer",)),)})
        required = {"tool": 100.0}
        tool_fallback.shift_unmet_tools(required, {"farm": 100.0}, recipes, {"tool": ["forge"]}, {"forge": 40.0})
        self.assertAlmostEqual(required["tool"], 40.0)
        self.assertAlmostEqual(required["plank"], 60.0 * 3.0)


class SecondShareOnATileTests(unittest.TestCase):
    def test_a_second_share_of_the_runs_on_a_tile_adds_to_its_producer(self):
        recipe = Recipe("dig", {"ore": 1.0}, {}, {"labourer": 1.0})
        setup = types.SimpleNamespace(opening_prices={}, opening_wages={}, yield_factor_by_recipe_tile={})
        record = EconomyRecord.__new__(EconomyRecord)
        record.producers = {}
        wanted = {}
        with mock.patch.object(opening, "_has_people", lambda record_, tile: True), \
                mock.patch.object(opening, "_richest_class", lambda record_, tile: 0), \
                mock.patch.object(opening.opening_income, "working_share", lambda *args: 1.0):
            opening._add_producers(setup, record, recipe, {"tile": 30.0}, wanted, {})
            opening._add_producers(setup, record, recipe, {"tile": 70.0}, wanted, {})
        [producer] = record.producers.values()
        self.assertAlmostEqual(producer.capacity_runs, 100.0)
        self.assertAlmostEqual(producer.expected_sales, 100.0)


class SiteRoomTests(unittest.TestCase):
    """A deposit's yearly room is the larger of its working share and the rate the data say it was worked at."""

    def room_of(self, size, history_rate, share=0.004):
        row = {"id": "mine", "tile_id": "tile"}
        return rules.priced_row(row, size, 0.0, 0.0, size * share, history_rate, 0.0)["room_tonnes_per_year"]

    def test_the_data_rate_is_the_room_when_it_is_above_the_working_share(self):
        self.assertAlmostEqual(self.room_of(1_000_000.0, 8250.0), 8250.0)

    def test_the_working_share_is_the_room_when_the_data_rate_is_below_it(self):
        self.assertAlmostEqual(self.room_of(1_000_000.0, 100.0), 4000.0)

    def test_room_never_exceeds_what_is_left_in_the_deposit(self):
        self.assertAlmostEqual(self.room_of(5.0, 8250.0), 5.0)

    def test_the_shipped_iron_deposits_work_at_the_rates_that_sum_to_the_empires_stated_output(self):
        deposits = deposit_model.load_deposits("iron")
        self.assertAlmostEqual(sum(deposit.quantity_tonnes_per_year for deposit in deposits), 82500.0)
        self.assertGreater(len(deposits), 1)


if __name__ == "__main__":
    unittest.main()
