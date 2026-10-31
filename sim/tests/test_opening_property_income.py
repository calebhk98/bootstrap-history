"""The opening hands each class the property income its income figure contains, so the first year's spending rule sees
the same income a later year sees (last year's rent and dividends) and a resting opening does not pile up cash.
A plain function on hand-written cohorts; no game."""
import unittest

from sim.economy import opening_income
from sim.economy.households_cohort import Cohort

QUICK_TOPIC = True


class OpeningPropertyIncomeTests(unittest.TestCase):
    def test_the_non_labour_share_of_a_tiles_income_goes_to_classes_by_what_they_own(self):
        cohorts = {"a": Cohort("a", "t", 0, 100.0, 50.0, 0.25), "b": Cohort("b", "t", 1, 100.0, 50.0, 0.75)}
        paid = opening_income.property_income_of(cohorts, per_head=10.0, labour_share=0.8)
        self.assertAlmostEqual(paid["a"], 2000.0 * 0.2 * 0.25)
        self.assertAlmostEqual(paid["b"], 2000.0 * 0.2 * 0.75)

    def test_a_tile_paying_only_labour_has_no_property_income(self):
        cohorts = {"a": Cohort("a", "t", 0, 100.0, 50.0, 1.0)}
        self.assertEqual(opening_income.property_income_of(cohorts, per_head=10.0, labour_share=1.0), {})

    def test_property_income_and_wages_add_up_to_the_income_figure(self):
        cohorts = {"a": Cohort("a", "t", 0, 100.0, 30.0, 0.5), "b": Cohort("b", "t", 1, 100.0, 70.0, 0.5)}
        income = opening_income.with_income(cohorts, 10.0, 0.6)
        property_income = opening_income.property_income_of(cohorts, 10.0, 0.6)
        labour = {agent: income[agent].last_year_income - property_income.get(agent, 0.0) for agent in cohorts}
        self.assertAlmostEqual(labour["a"], 2000.0 * 0.6 * 0.3)
        self.assertAlmostEqual(labour["b"], 2000.0 * 0.6 * 0.7)


if __name__ == "__main__":
    unittest.main()
