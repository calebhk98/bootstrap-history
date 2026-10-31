"""Complaint 607: the opening's income is the value of what its working hands can make."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import opening_income


def recipes():
    return {"farm": types.SimpleNamespace(labour_hours={"labourer": 10.0}),
            "mine": types.SimpleNamespace(labour_hours={"miner": 6.0, "smith": 4.0})}


class ProducibleShareTests(unittest.TestCase):
    def test_runs_whose_hours_fit_the_hands_are_all_producible(self):
        self.assertEqual(opening_income.producible_share({"farm": 5.0}, recipes(), 100.0), 1.0)

    def test_runs_needing_twice_the_hands_are_half_producible(self):
        self.assertEqual(opening_income.producible_share({"farm": 10.0, "mine": 10.0}, recipes(), 100.0), 100.0 / 200.0)

    def test_all_trades_of_a_recipe_count(self):
        self.assertEqual(opening_income.producible_share({"mine": 20.0}, recipes(), 100.0), 0.5)

    def test_no_runs_need_no_hands(self):
        self.assertEqual(opening_income.producible_share({}, recipes(), 0.0), 1.0)

    def test_no_hands_make_nothing(self):
        self.assertEqual(opening_income.producible_share({"farm": 1.0}, recipes(), 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
