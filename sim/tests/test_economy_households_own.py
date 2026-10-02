"""A household's own plot: hours it keeps back from the labour market to grow what it could not get."""
import unittest

from sim.economy.households_cohort import Cohort
from sim.economy import households_own
from sim.economy.households_own import hours_for_own_plan, next_own_plan, withhold_hours
from sim.economy.types import LabourOffer

OPTIONS = {"food": [(2.0, "grow_grain", "grain", 1.0)]}     # two hours a need unit at fertility one


def cohort(plan=None):
    return Cohort("household:t:0", "t", 0, 100.0, 50.0, 0.3, own_plan_by_need=dict(plan or {}))


class OwnPlanTests(unittest.TestCase):
    def test_hours_grow_the_plan_at_this_tiles_fertility(self):
        self.assertAlmostEqual(hours_for_own_plan(cohort({"food": 10.0}), OPTIONS, 0.5), 40.0)

    def test_a_household_with_no_plan_keeps_nothing_back(self):
        self.assertEqual(hours_for_own_plan(cohort(), OPTIONS, 0.5), 0.0)

    def test_a_need_it_cannot_grow_keeps_nothing_back(self):
        self.assertEqual(hours_for_own_plan(cohort({"tools": 10.0}), OPTIONS, 0.5), 0.0)

    def test_the_plan_keeps_what_it_grew_and_adds_this_years_shortfall(self):
        # growing only last year's shortfall would leave it short again the year after
        plan = next_own_plan({"food": 60.0}, {"food": 20.0})
        self.assertAlmostEqual(plan["food"], 60.0 * (1.0 - households_own.OWN_PLAN_RELEASE_SHARE_PER_YEAR) + 20.0)

    def test_with_markets_feeding_it_the_plan_fades(self):
        plan = {"food": 60.0}
        for _year in range(60):
            plan = next_own_plan(plan, {})
        self.assertLess(plan.get("food", 0.0), 1.0)


class WithholdTests(unittest.TestCase):
    def test_offers_shrink_in_proportion_and_the_kept_hours_are_returned(self):
        offers = [LabourOffer("w", "smith", "a", 60.0, 1.0), LabourOffer("w", "miner", "a", 40.0, 1.0)]
        kept_offers, kept = withhold_hours(offers, {"w": 50.0})
        self.assertEqual([offer.hours for offer in kept_offers], [30.0, 20.0])
        self.assertEqual(kept, {"w": 50.0})

    def test_it_cannot_keep_more_than_it_has(self):
        kept_offers, kept = withhold_hours([LabourOffer("w", "smith", "a", 60.0, 1.0)], {"w": 500.0})
        self.assertEqual([offer.hours for offer in kept_offers], [0.0])
        self.assertEqual(kept, {"w": 60.0})


if __name__ == "__main__":
    unittest.main()
