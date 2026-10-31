"""Complaint 644: an entrant plans on the hours its crew will need under on-the-job learning, not the booked hours."""
QUICK_TOPIC = True

import types
import unittest
import unittest.mock

from sim.economy import entry, entry_practice, labour_state, practice
from sim.economy.producers_close import LOSS_YEARS_BEFORE_EXIT
from sim.economy.types import Recipe
from sim.tests.test_economy_producers import View

FLOOR = practice.SOURCE_TASK_FLOOR_FRACTION
SALT = Recipe("mine_salt", {"salt": 10.0}, {}, {"hand": 4.0})


def hands(recipe):
    return recipe.labour_hours["hand"]


class PlannedRecipeTests(unittest.TestCase):
    def test_an_entrant_with_no_peers_and_no_runs_needs_a_first_attempts_hours_every_year(self):
        self.assertAlmostEqual(hands(entry_practice.planned_recipe(SALT, [], 0.0)), 4.0 / FLOOR)

    def test_an_entrant_who_reaches_the_floor_in_its_first_year_averages_one_hard_year_and_easy_ones(self):
        hours = hands(entry_practice.planned_recipe(SALT, [], 1.0e9))
        self.assertAlmostEqual(hours, (4.0 / FLOOR + 4.0 * (LOSS_YEARS_BEFORE_EXIT - 1)) / LOSS_YEARS_BEFORE_EXIT)

    def test_an_entrant_beside_established_peers_needs_the_booked_hours(self):
        self.assertIs(entry_practice.planned_recipe(SALT, [{}, {}], 5.0), SALT)

    def test_the_first_years_hours_are_a_first_attempts_where_nobody_makes_it(self):
        self.assertAlmostEqual(hands(entry_practice.first_year_recipe(SALT, [])), 4.0 / FLOOR)


class EntryDecisionTests(unittest.TestCase):
    def plans(self, unmet, peers):
        view = View(prices={"salt": 0.2}, wages={"hand": 0.2})
        market = {("salt", "area"): entry.UnmetDemand("salt", "area", "anchor", unmet)}
        return entry.entry_plans({"mine_salt": SALT}, view, market, crews_of=lambda recipe_id: peers)

    def test_a_works_that_pays_on_the_booked_hours_but_not_on_its_first_attempts_does_not_enter(self):
        self.assertEqual(self.plans(10.0, []), [])

    def test_a_works_big_enough_to_learn_inside_the_horizon_enters_on_the_mean_of_its_years(self):
        self.assertEqual([plan.recipe_id for plan in self.plans(1.0e6, [])], ["mine_salt"])

    def test_a_works_beside_established_peers_enters_on_the_booked_hours(self):
        self.assertEqual([plan.recipe_id for plan in self.plans(10.0, [{}])], ["mine_salt"])


class HoursNeededTests(unittest.TestCase):
    def test_a_producers_hours_are_those_its_crew_has_practised(self):
        setup = types.SimpleNamespace(recipes={"mine_salt": SALT}, capital_tile="capital")
        producer = types.SimpleNamespace(recipe_id="mine_salt", tile="field", expected_sales=2.0, crew_runs={"hand": 1.0})
        record = types.SimpleNamespace(currency=None, producers={"a": producer})
        mint = types.SimpleNamespace(capacity_fine_kilograms=lambda *_args: 0.0)
        mint_labour = types.SimpleNamespace(capacity_hours=lambda *_args: {})
        with unittest.mock.patch.object(labour_state, "mint", mint), \
                unittest.mock.patch.object(labour_state, "mint_labour", mint_labour):
            needed = labour_state.producers_hours_needed(setup, record)
        self.assertAlmostEqual(needed[labour_state.labour_area("field")]["hand"], 2.0 * 4.0 / FLOOR)


if __name__ == "__main__":
    unittest.main()
