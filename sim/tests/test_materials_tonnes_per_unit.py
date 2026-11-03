"""`ProjectBill.tonnes_per_unit` and `Holding.tonnes_per_unit`: tonnes in a unit are the markets `unit_mass_kg` view over a thousand."""
QUICK_TOPIC = True

import math
import unittest

from sim.living_stock.holding import Holding
from sim.materials.project_bill import ProjectBill
from sim.tests import module_harness

MASS = {"stone": 250.0, "land": math.inf}


class TonnesPerUnit(unittest.TestCase):
	def test_a_bill_counts_a_unit_at_the_economys_mass_for_it(self):
		bill = module_harness.part(ProjectBill, views={"unit_mass_kg": MASS.get})
		self.assertEqual(bill.tonnes_per_unit("stone"), 0.25)

	def test_a_bill_counts_a_unit_with_no_mass_as_moving_no_tonnes(self):
		bill = module_harness.part(ProjectBill, views={"unit_mass_kg": MASS.get})
		self.assertEqual(bill.tonnes_per_unit("land"), 0.0)

	def test_living_stock_counts_a_unit_at_the_economys_mass_for_it(self):
		holding = module_harness.part(Holding, views={"unit_mass_kg": MASS.get})
		self.assertEqual(holding.tonnes_per_unit("stone"), 0.25)
		self.assertEqual(holding.kilograms_per_unit("stone"), 250.0)


if __name__ == "__main__":
	unittest.main()
