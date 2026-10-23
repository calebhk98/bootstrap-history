"""Complaint 554, Complaint 640: the rules of the baseline checks, called on built yearly accounts: feasibility names
each way a year's books can overdraw, and food_eaten_over_need reads the last year's tiles. The statistic of the
settling report is in test_series_settling_rule."""
QUICK_TOPIC = True

import unittest

from sim.economy.baseline_checks import feasibility, food_eaten_over_need
from sim.economy.settling import SERIES, settling_report
from sim.economy.year_accounts import GoodAccount, TileAccount, YearAccounts


def year(number, **figures):
    return YearAccounts(number, {"grain": GoodAccount(**figures)})


class FeasibilityTests(unittest.TestCase):
    def test_books_that_close_are_feasible(self):
        accounts = [year(0, production=100.0, final_consumption_bought=90.0, stock_at_start=10.0, stock_change=10.0)]
        self.assertEqual(feasibility(accounts), [])

    def test_a_good_used_beyond_what_was_made_and_held_is_named_with_its_year_and_amount(self):
        found = feasibility([year(3, production=100.0, final_consumption_bought=150.0, stock_at_start=10.0,
                                  stock_change=-10.0)])
        overdraw = [item for item in found if item.kind == "uses_exceed_supply"]
        self.assertEqual([(item.year, item.good) for item in overdraw], [(3, "grain")])
        self.assertAlmostEqual(overdraw[0].amount, 40.0)

    def test_a_stock_change_the_flows_do_not_explain_is_named(self):
        found = feasibility([year(1, production=100.0, final_consumption_bought=90.0, stock_at_start=10.0,
                                  stock_change=25.0)])
        self.assertEqual([item.kind for item in found], ["unexplained_stock_change"])
        self.assertAlmostEqual(found[0].amount, 15.0)

    def test_a_stock_driven_below_nothing_is_named(self):
        found = feasibility([year(2, production=100.0, final_consumption_bought=100.0, stock_at_start=5.0,
                                  stock_change=-20.0)])
        self.assertIn("negative_stock", [item.kind for item in found])

    def test_float_dust_beside_the_flows_is_not_an_overdraw(self):
        accounts = [year(0, production=1.8e6, final_consumption_bought=1.8e6 + 1e-3, stock_change=-1e-3)]
        self.assertEqual(feasibility(accounts), [])


class FoodEatenTests(unittest.TestCase):
    def test_it_reads_each_tile_of_the_last_year_only(self):
        first = YearAccounts(0, tiles=[TileAccount("a", 10.0, 2.0, 0.0)])
        last = YearAccounts(1, tiles=[TileAccount("a", 10.0, 2.0, 3.0), TileAccount("b", 5.0, 4.0, 2.0)])
        self.assertEqual(food_eaten_over_need([first, last]), {"a": 1.5, "b": 0.5})

    def test_no_years_give_no_tiles(self):
        self.assertEqual(food_eaten_over_need([]), {})


class SettlingReportTests(unittest.TestCase):
    def test_the_report_names_the_four_series_in_order_with_finite_statistics(self):
        rows = [{"price_level": 1.0, "wage": 2.0, "money_supply": 100.0, "rate": 0.05} for _year in range(40)]
        report = settling_report(rows)
        self.assertEqual([item.name for item in report], [name for name, _ratio in SERIES])
        self.assertTrue(all(item.settled for item in report))


if __name__ == "__main__":
    unittest.main()
