"""What a worker must earn and a year's jump in the cost of the floors: the search rules read the cost as priced, the
clearing rules move it from last year's by no more than a market's price may move in a year."""

QUICK_TOPIC = True

import unittest

from sim.economy import outside_option_step, price_step, rule_sets


class AsPriced(unittest.TestCase):
    def test_this_years_figures_whatever_last_years_were(self):
        self.assertEqual(outside_option_step.as_priced({"north": 100.0}, {"north": 2000.0, "south": 90.0}), {"north": 2000.0, "south": 90.0})


class WithinAYearsMove(unittest.TestCase):
    LIMIT = price_step.PRICE_MOVE_LIMIT_PER_YEAR

    def test_a_cost_that_jumps_many_fold_rises_by_what_a_price_may_in_a_year(self):
        stepped = outside_option_step.within_a_years_move({"north": 100.0}, {"north": 2000.0})
        self.assertAlmostEqual(stepped["north"], 100.0 * (1.0 + self.LIMIT))

    def test_a_cost_that_collapses_falls_by_the_same_factor(self):
        stepped = outside_option_step.within_a_years_move({"north": 100.0}, {"north": 1.0})
        self.assertAlmostEqual(stepped["north"], 100.0 / (1.0 + self.LIMIT))

    def test_a_small_move_is_taken_whole(self):
        self.assertEqual(outside_option_step.within_a_years_move({"north": 100.0}, {"north": 104.0}), {"north": 104.0})

    def test_a_tile_with_no_figure_last_year_takes_this_years(self):
        self.assertEqual(outside_option_step.within_a_years_move({}, {"north": 2000.0}), {"north": 2000.0})
        self.assertEqual(outside_option_step.within_a_years_move({"north": 0.0}, {"north": 2000.0}), {"north": 2000.0})

    def test_a_tile_that_is_gone_this_year_is_dropped(self):
        self.assertEqual(outside_option_step.within_a_years_move({"north": 100.0, "south": 90.0}, {"south": 91.0}), {"south": 91.0})


class Rules(unittest.TestCase):
    def test_which_rule_each_set_runs(self):
        self.assertIs(rule_sets.RULE_SETS["search"].outside_option_stepped, outside_option_step.as_priced)
        self.assertIs(rule_sets.RULE_SETS["clearing"].outside_option_stepped, outside_option_step.within_a_years_move)


if __name__ == "__main__":
    unittest.main()
