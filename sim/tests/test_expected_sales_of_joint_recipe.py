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


if __name__ == "__main__":
    unittest.main()
