"""The hours a household offers to the market are a choice against what an hour yields at home (Complaints 473, 608)."""

QUICK_TOPIC = True

import unittest

from sim.economy import households_hours_offered as rule
from sim.world.need_basket import Basket, NeedSpec
from sim.economy.households_cohort import Cohort
from sim.economy.households_own import own_production
from sim.economy.types import Recipe
from sim.world.need_demand import NEED_SUBSTITUTION_ELASTICITY
from sim.world.shared_constants import LABOUR_OUTPUT_ELASTICITY

HOURS, RETURN, USABLE = 2000.0, 0.5, 1500.0


class PlotHoursKeptTests(unittest.TestCase):
    def offered(self, wage, plot_return=RETURN, usable=USABLE):
        return HOURS - rule.plot_hours_kept(HOURS, wage, plot_return, usable)

    def test_a_higher_wage_offers_more_hours(self):
        offered = [self.offered(wage) for wage in (0.1, 0.3, 0.5, 1.0, 3.0)]
        self.assertEqual(offered, sorted(offered))
        self.assertLess(offered[0], offered[-1])

    def test_a_wage_below_the_plots_return_keeps_every_usable_hour(self):
        self.assertAlmostEqual(self.offered(0.1), HOURS - USABLE)

    def test_a_household_with_no_plot_offers_all_its_working_hours(self):
        self.assertEqual(self.offered(0.01, usable=0.0), HOURS)
        self.assertEqual(self.offered(0.01, plot_return=0.0), HOURS)

    def test_the_next_hour_at_home_is_worth_the_wage_at_the_hours_it_keeps(self):
        kept = rule.plot_hours_kept(HOURS, 0.8, RETURN, USABLE)
        self.assertGreater(kept, 0.0)
        self.assertLess(kept, USABLE)
        self.assertAlmostEqual(RETURN * (HOURS / kept) ** (1.0 - LABOUR_OUTPUT_ELASTICITY), 0.8)

    def test_a_wage_that_is_not_positive_keeps_every_usable_hour(self):
        self.assertEqual(rule.plot_hours_kept(HOURS, 0.0, RETURN, USABLE), USABLE)


class UnhiredHoursTests(unittest.TestCase):
    def test_the_unhired_hours_grow_what_the_household_eats(self):
        recipe = Recipe("grow", {"grain": 100.0}, {}, {"labourer": 10.0})
        basket = Basket((NeedSpec("food", 50.0, 0.5, (("grain", 1.0),)),), NEED_SUBSTITUTION_ELASTICITY, {})
        cohort = Cohort(agent_id="c", tile="t", income_class=0, people=1.0, working_people=1.0, ownership_share=0.0)
        options = {"food": [(10.0 / 100.0, "grow", "grain", 1.0)]}
        home = 80.0     # the hours no employer took
        moves, grown, _units = own_production(cohort, home, options, {"grow": recipe}, 1.0, basket, {"grow": 1.0}, 10.0)
        self.assertGreater(grown.get("grain", 0.0), 0.0)
        self.assertEqual(moves[0].good, "grain")


if __name__ == "__main__":
    unittest.main()
