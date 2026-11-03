"""`keep_deliveries`: goods a buyer that keeps its purchases bought join its stores in tonnes, counted at the mass the caller gives a unit."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.actors import delivered_goods


def buyer(keeps):
	return SimpleNamespace(keeps_purchases=keeps, record=SimpleNamespace(stores="stores"))


class KeepDeliveries(unittest.TestCase):
	def keep(self, known, delivered, tonnes_per_unit):
		added = []
		with mock.patch.object(delivered_goods.stock_keeping, "add_delivery", lambda stores, tonnes: added.append((stores, tonnes))):
			delivered_goods.keep_deliveries(known, delivered, tonnes_per_unit)
		return added

	def test_units_join_the_stores_as_tonnes_at_the_given_mass_of_a_unit(self):
		added = self.keep({"a": buyer(True)}, {"a": {"iron": 4.0, "stone": 2.0}}, {"iron": 0.5, "stone": 3.0}.get)
		self.assertEqual(added, [("stores", {"iron": 2.0, "stone": 6.0})])

	def test_a_good_with_no_mass_per_unit_is_not_carried_into_the_stores(self):
		added = self.keep({"a": buyer(True)}, {"a": {"iron": 4.0, "land": 9.0}}, {"iron": 0.5}.get)
		self.assertEqual(added, [("stores", {"iron": 2.0})])

	def test_a_buyer_that_does_not_keep_its_purchases_gets_nothing(self):
		self.assertEqual(self.keep({"a": buyer(False)}, {"a": {"iron": 4.0}}, {"iron": 0.5}.get), [])


if __name__ == "__main__":
	unittest.main()
