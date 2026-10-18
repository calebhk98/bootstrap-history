"""Complaint 550: a recipe that states the crew of one establishment opens as that many workshops on a tile
(capacity over one establishment's runs, at least one); a recipe that does not opens as one."""

QUICK_TOPIC = True

import types as pytypes
import unittest

from sim.economy import establishment, opening
from sim.economy.households_cohort import Cohort
from sim.economy.recipes import recipe_from_entry
from sim.engine import validate_production
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

TILE = "t1"
HOURS_PER_RUN = 100.0


def entry(**extra):
    return dict({"outputs": {"grain": 1.0}, "inputs": {}, "labour_hours": {"labourer": HOURS_PER_RUN}}, **extra)


def opened(recipe, capacity):
    setup = pytypes.SimpleNamespace(opening_prices={"grain": 1.0}, opening_wages={"labourer": 0.001},
                                    yield_factor_by_recipe_tile={})
    record = pytypes.SimpleNamespace(producers={}, cohorts={
        "household:t1:0": Cohort("household:t1:0", TILE, 0, 100.0, 50.0, 0.5, last_year_income=1.0)})
    opening._add_producers(setup, record, recipe, {TILE: capacity}, {}, {})
    return next(iter(record.producers.values()))


class EstablishmentSizeTests(unittest.TestCase):
    def test_a_stated_crew_sets_the_runs_of_one_establishment(self):
        recipe = recipe_from_entry("grain", entry(establishment_workers=2))
        self.assertAlmostEqual(establishment.runs_per_establishment(recipe), 2 * HOURS_PER_PERSON_YEAR / HOURS_PER_RUN)

    def test_capacity_opens_as_that_many_workshops(self):
        recipe = recipe_from_entry("grain", entry(establishment_workers=2))
        size = establishment.runs_per_establishment(recipe)
        self.assertEqual(opened(recipe, 7.0 * size).workshops, 7)

    def test_less_than_one_establishment_is_one_workshop(self):
        recipe = recipe_from_entry("grain", entry(establishment_workers=2))
        self.assertEqual(opened(recipe, 0.3 * establishment.runs_per_establishment(recipe)).workshops, 1)

    def test_a_recipe_without_a_stated_crew_opens_as_one(self):
        recipe = recipe_from_entry("grain", entry())
        self.assertEqual(establishment.runs_per_establishment(recipe), 0.0)
        self.assertEqual(opened(recipe, 1e9).workshops, 1)


class SchemaTests(unittest.TestCase):
    def problems(self, **extra):
        return validate_production.check_establishment_workers("grain", entry(**extra))

    def test_a_positive_crew_validates(self):
        self.assertEqual(self.problems(establishment_workers=3), [])
        self.assertEqual(self.problems(), [])

    def test_a_bad_crew_is_reported(self):
        for bad in (0, -1, "two", True, float("inf")):
            self.assertTrue(self.problems(establishment_workers=bad), bad)

    def test_a_crew_with_no_labour_to_size_is_reported(self):
        self.assertTrue(validate_production.check_establishment_workers(
            "grain", {"outputs": {"grain": 1.0}, "establishment_workers": 2}))


if __name__ == "__main__":
    unittest.main()
