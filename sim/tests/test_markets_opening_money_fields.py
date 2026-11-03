"""`in_units` counts every opening money field in the economy's unit (one hour of the unskilled trade's wage)."""
QUICK_TOPIC = True

import unittest

from sim.markets.port_setup import OPENING_MONEY_FIELDS, in_units


class OpeningMoneyFields(unittest.TestCase):
	def test_every_money_field_is_divided_by_the_unskilled_wage(self):
		opening = {field: {"x": 8.0} for field in OPENING_MONEY_FIELDS}
		opening["wages"] = {"labourer": 2.0, "x": 8.0}
		opening["unskilled_trade"] = "labourer"
		counted = in_units(opening)
		for field in OPENING_MONEY_FIELDS:
			self.assertEqual(counted[field]["x"], 4.0, field)


if __name__ == "__main__":
	unittest.main()
