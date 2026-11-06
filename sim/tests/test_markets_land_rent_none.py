"""Where the land market let no land the rent reads are None, not a rent of zero that would make land free."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.markets import reads_households
from sim.markets.reads_households import HouseholdReads


class LandRentNone(unittest.TestCase):
	def reads(self):
		return HouseholdReads(SimpleNamespace(economy=lambda: "economy"))

	def test_no_land_let_is_no_mean_rent(self):
		with mock.patch.object(reads_households.economy_api, "land_rent_per_hectare", return_value=None), \
				mock.patch.object(reads_households.economy_api, "coin_per_unit", return_value=2.0):
			self.assertIsNone(self.reads().land_rent_per_hectare())

	def test_a_mean_rent_is_counted_in_coin(self):
		with mock.patch.object(reads_households.economy_api, "land_rent_per_hectare", return_value=3.0), \
				mock.patch.object(reads_households.economy_api, "coin_per_unit", return_value=2.0):
			self.assertEqual(self.reads().land_rent_per_hectare(), 6.0)

	def test_no_land_let_anywhere_is_no_rent_on_a_tile(self):
		with mock.patch.object(reads_households.economy_api, "land_rent_at_tile", return_value=None), \
				mock.patch.object(reads_households.economy_api, "coin_per_unit", return_value=2.0):
			self.assertIsNone(self.reads().land_rent_at_tile("t"))


if __name__ == "__main__":
	unittest.main()
