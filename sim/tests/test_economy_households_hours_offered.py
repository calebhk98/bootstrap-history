"""The hours a household offers to the market are a choice against what an hour yields at home (Complaints 473, 608)."""

QUICK_TOPIC = True

import unittest

from sim.economy import households_hours_offered as rule
from sim.economy.households_basket import Basket, NeedSpec
from sim.economy.households_cohort import Cohort
from sim.economy.households_own import own_production
from sim.economy.types import Recipe
from sim.world.need_demand import NEED_SUBSTITUTION_ELASTICITY
from sim.world.shared_constants import LABOUR_OUTPUT_ELASTICITY

HOURS, RETURN, USABLE = 2000.0, 0.5, 1500.0


class PlotHoursKeptTests(unittest.TestCase):
    def offered(self, wage, plot_return=RETURN, usable=USABLE):
        return rule.hours_offered(HOURS, rule.plot_hours_kept(HOURS, wage, plot_return, usable))

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

    def test_the_wage_that_offers_a_quantity_inverts_the_choice(self):
        offered = self.offered(0.8)
        self.assertAlmostEqual(rule.wage_that_offers(HOURS, offered, RETURN, USABLE), 0.8)
        self.assertIsNone(rule.wage_that_offers(HOURS, HOURS - USABLE - 1.0, RETURN, USABLE))
        self.assertIsNone(rule.wage_that_offers(HOURS, HOURS, RETURN, USABLE))

    def test_a_wage_that_is_not_positive_keeps_every_usable_hour(self):
        self.assertEqual(rule.plot_hours_kept(HOURS, 0.0, RETURN, USABLE), USABLE)


class UnhiredHoursTests(unittest.TestCase):
    def test_hours_no_employer_took_go_back_to_own_production_not_lost(self):
        self.assertEqual(rule.unsold_hours_to_home(1000.0, 400.0), (400.0, 600.0))

    def test_the_unhired_hours_grow_what_the_household_eats(self):
        recipe = Recipe("grow", {"grain": 100.0}, {}, {"labourer": 10.0})
        basket = Basket((NeedSpec("food", 50.0, 0.5, (("grain", 1.0),)),), NEED_SUBSTITUTION_ELASTICITY, {})
        cohort = Cohort(agent_id="c", tile="t", income_class=0, people=1.0, working_people=1.0, ownership_share=0.0)
        options = {"food": [(10.0 / 100.0, "grow", "grain", 1.0)]}
        _sold, home = rule.unsold_hours_to_home(100.0, 20.0)
        moves, grown, _units = own_production(cohort, home, options, {"grow": recipe}, 1.0, basket, {"grow": 1.0}, 10.0)
        self.assertGreater(grown.get("grain", 0.0), 0.0)
        self.assertEqual(moves[0].good, "grain")


class LeisureTests(unittest.TestCase):
    """Leisure is an hour valued by a declared preference: the share of free hours kept falls smoothly as the wage rises."""
    ANCHOR, ELASTICITY = 0.6, 2.0

    def market_hours(self, wage, plot_return=RETURN, usable=USABLE, anchor=ANCHOR):
        kept = rule.plot_hours_kept(HOURS, wage, plot_return, usable)
        free = HOURS - kept
        return free - rule.leisure_hours_kept(free, wage, anchor, self.ELASTICITY)

    def test_a_higher_wage_offers_more_hours_smoothly(self):
        wages = [0.2 * 1.01 ** step for step in range(400)]
        for usable in (USABLE, 0.0):
            offered = [self.market_hours(wage, usable=usable) for wage in wages]
            self.assertEqual(offered, sorted(offered))
            for before, after in zip(offered, offered[1:]):
                self.assertLess(after / before - 1.0, 0.1)        # one per cent more wage never jumps the hours

    def test_with_no_plot_hours_offered_rise_no_faster_than_the_leisure_elasticity(self):
        for wage in (0.2, 0.6, 1.0, 3.0):
            ratio = self.market_hours(wage * 1.001, usable=0.0) / self.market_hours(wage, usable=0.0)
            self.assertLess(ratio - 1.0, self.ELASTICITY * 0.001 * 1.01)

    def test_half_the_free_hours_go_to_leisure_at_the_anchor_wage(self):
        self.assertAlmostEqual(rule.leisure_hours_kept(1000.0, self.ANCHOR, self.ANCHOR, self.ELASTICITY), 500.0)

    def test_without_an_anchor_no_hour_is_leisure(self):
        self.assertEqual(rule.leisure_hours_kept(1000.0, 1.0, None, self.ELASTICITY), 0.0)
        self.assertEqual(rule.leisure_hours_kept(1000.0, 1.0, 0.0, self.ELASTICITY), 0.0)

    def test_the_anchor_that_offers_the_hours_wanted_inverts_the_choice(self):
        anchor = rule.leisure_anchor_wage(1000.0, 360.0, 1.2, self.ELASTICITY)
        self.assertAlmostEqual(rule.leisure_hours_kept(1000.0, 1.2, anchor, self.ELASTICITY), 360.0)

    def test_no_anchor_offers_more_hours_than_there_are_free(self):
        self.assertIsNone(rule.leisure_anchor_wage(1000.0, 1000.0, 1.2, self.ELASTICITY))     # more leisure wanted than there are hours
        self.assertIsNone(rule.leisure_anchor_wage(1000.0, 1200.0, 1.2, self.ELASTICITY))
        self.assertIsNone(rule.leisure_anchor_wage(1000.0, 0.0, 1.2, self.ELASTICITY))

    def test_hours_offered_equal_the_hours_hired_at_the_wage_the_anchor_was_set_at(self):
        wage, hired = 1.0, 1100.0
        free = HOURS - rule.plot_hours_kept(HOURS, wage, RETURN, USABLE)
        anchor = rule.leisure_anchor_wage(free, free - hired, wage, self.ELASTICITY)
        self.assertAlmostEqual(self.market_hours(wage, anchor=anchor), hired)

    def test_a_few_per_cent_of_excess_hours_moves_the_wage_a_few_per_cent_not_a_third(self):
        wage, hired = 1.0, 1100.0
        free = HOURS - rule.plot_hours_kept(HOURS, wage, RETURN, USABLE)
        anchor = rule.leisure_anchor_wage(free, free - hired, wage, self.ELASTICITY)
        for excess in (0.03, 0.05):
            target = hired / (1.0 + excess)       # hours offered fall to this when the wage falls enough to remove the excess
            low_wage, high_wage = 0.3, wage
            for _step in range(80):
                middle = (low_wage + high_wage) / 2.0
                if self.market_hours(middle, anchor=anchor) > target:
                    high_wage = middle
                else:
                    low_wage = middle
            self.assertGreater(high_wage, 1.0 - 3.0 * excess)     # the wage falls by a few per cent, not by a third


if __name__ == "__main__":
    unittest.main()
