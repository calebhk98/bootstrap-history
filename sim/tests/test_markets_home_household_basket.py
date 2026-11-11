"""`HouseholdNeeds.home_household_tonnes` builds the home households' demand on the civilisation's climate basket, the one the
actors' budgets read, not the model's default basket."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.markets import household_needs
from sim.markets.household_views import HouseholdNeeds


class HomeHouseholdBasket(unittest.TestCase):
	def test_the_demand_is_asked_for_on_the_climate_basket(self):
		views = object.__new__(HouseholdNeeds)
		views._household_model = lambda: ("model", frozenset())
		views.opening_population = lambda: 10.0
		views.tonnes_per_unit = lambda material: 1.0
		views._civilisation_basket = lambda base: ("climate basket of", base)
		with mock.patch.object(household_needs, "demand_by_material", return_value={}) as demand:
			views.home_household_tonnes({"wheat_kg": 1.0})
		self.assertEqual(demand.call_args.args[-1], ("climate basket of", "model"))


if __name__ == "__main__":
	unittest.main()
