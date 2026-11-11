"""Complaint 492: the state's masonry works take the labour of a laid-wall service recipe, trade by trade. One function per
check, inputs written out."""
QUICK_TOPIC = True

import unittest

from sim.agents import state_masonry
from sim.world import state_masonry as recipe_rules


class PersonYears(unittest.TestCase):
    def test_a_square_metre_takes_the_recipe_hours_over_the_wall_it_holds(self):
        years = recipe_rules.person_years_per_square_metre({"mason": 20.0, "labourer": 40.0}, 1.5, 2000.0)
        self.assertAlmostEqual(years["mason"], 20.0 * 1.5 / 2000.0)
        self.assertAlmostEqual(years["labourer"], 40.0 * 1.5 / 2000.0)

    def test_a_trade_with_no_hours_is_left_out(self):
        self.assertEqual(recipe_rules.person_years_per_square_metre({"mason": 0.0}, 1.5, 2000.0), {})

    def test_a_trade_nobody_practises_is_done_by_the_fallback_trade(self):
        folded = recipe_rules.fold_absent_trades({"mason": 1.0, "labourer": 2.0}, {"mason": False, "labourer": True}, "labourer")
        self.assertEqual(folded, {"labourer": 3.0})

    def test_the_service_is_named_in_data(self):
        self.assertTrue(recipe_rules.service_material())


class Raisable(unittest.TestCase):
    CREW = {"mason": 0.02, "labourer": 0.04}
    WAGE = {"mason": 10.0, "labourer": 5.0}

    def test_the_gap_limits_when_money_and_people_allow_more(self):
        self.assertEqual(state_masonry.square_metres_raisable(7.0, 1.0e9, self.CREW, self.WAGE, {"mason": 1.0e9, "labourer": 1.0e9}), 7.0)

    def test_the_money_limits_at_each_trades_wage(self):
        cost = 0.02 * 10.0 + 0.04 * 5.0
        self.assertAlmostEqual(state_masonry.square_metres_raisable(1.0e9, 8.0, self.CREW, self.WAGE, {"mason": 1.0e9, "labourer": 1.0e9}), 8.0 / cost)

    def test_the_scarcest_trade_limits(self):
        self.assertAlmostEqual(state_masonry.square_metres_raisable(1.0e9, 1.0e9, self.CREW, self.WAGE, {"mason": 1.0e9, "labourer": 2.0}), 2.0 / 0.04)

    def test_no_money_raises_nothing(self):
        self.assertEqual(state_masonry.square_metres_raisable(5.0, 0.0, self.CREW, self.WAGE, {"mason": 9.0, "labourer": 9.0}), 0.0)


if __name__ == "__main__":
    unittest.main()
