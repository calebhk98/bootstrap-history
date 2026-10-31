"""Labour-demand diagnosis: a joint recipe's expected sales follow the output made in the largest quantity
(`producers.main_output`), not the output that earns. A grain farm whose run makes more straw than grain, sells all
its grain and no straw, is read as having sold nothing, so its expected sales (and so its hours wanted) halve."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers, year_close
from sim.economy.types import Recipe
from sim.economy.year_ledger import YearLedger

FARM = Recipe("farm", {"straw": 1500.0, "grain": 900.0}, {}, {"hand": 200.0})


class Book:
    def stock(self, agent, good, tile):
        return 0.0       # sold out


class SalesOfAJointRecipeTests(unittest.TestCase):
    def test_a_farm_that_sold_all_its_grain_expects_to_go_on_selling_it(self):
        farm = producers.Producer("farm1", "owner", "farm", "tile", capacity_runs=100.0, expected_sales=100.0)
        ledger = YearLedger()
        ledger.sold[("farm1", "grain")] = 100.0 * 900.0       # every run's grain sold
        ledger.output[("farm1", "grain")] = 100.0 * 900.0
        ledger.output[("farm1", "straw")] = 100.0 * 1500.0     # the straw found no buyer
        after = year_close._with_sales(farm, FARM, ledger, Book(), lambda good, tile: "area", {})
        self.assertAlmostEqual(after.expected_sales, 100.0)

    def test_runs_sold_are_the_value_sold_over_the_value_of_a_run(self):
        ledger = YearLedger()
        ledger.sold[("farm1", "grain")] = 50.0 * 900.0       # half the grain, the straw unsold
        farm = producers.Producer("farm1", "owner", "farm", "tile", capacity_runs=100.0, expected_sales=100.0)
        runs = year_close.runs_sold(farm, FARM, ledger, Book(), lambda good, tile: "area", {},
                                    {"grain": 1.0, "straw": 0.001})
        self.assertAlmostEqual(runs, 50.0 * 900.0 / (900.0 + 1.5), places=6)

    def test_with_no_output_priced_the_output_that_sold_most_of_its_run_stands_for_it(self):
        ledger = YearLedger()
        ledger.sold[("farm1", "grain")] = 30.0 * 900.0
        farm = producers.Producer("farm1", "owner", "farm", "tile", capacity_runs=100.0, expected_sales=100.0)
        self.assertAlmostEqual(year_close.runs_sold(farm, FARM, ledger, Book(), lambda good, tile: "area", {}, {}), 30.0)

    def test_the_paying_output_is_the_one_with_most_value_not_most_weight(self):
        self.assertEqual(producers.paying_output(FARM, {"grain": 1.0, "straw": 0.001}), "grain")
        self.assertEqual(producers.paying_output(FARM, {}), "grain")       # no prices: first by name


class StockBindingTests(unittest.TestCase):
    def test_a_pile_of_a_minor_output_does_not_bind_though_the_others_do_not_cover_the_run(self):
        farm = producers.Producer("farm1", "owner", "farm", "tile", capacity_runs=100.0, expected_sales=10.0)

        class Stocked:
            def stock(self, agent, good, tile):
                return 1e9 if good == "straw" else 0.0
        runs = producers.runs_for_stock(farm, FARM, Stocked(), 1e6, {"grain": 1.0, "straw": 0.001})
        self.assertGreaterEqual(runs, 10.0)       # the grain's empty stock plans it, the unsold straw does not stop it


if __name__ == "__main__":
    unittest.main()
