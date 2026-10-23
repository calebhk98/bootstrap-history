"""Complaint 513: the hands kept on the land fall continuously with the value of a farm hour against the wage, and do not
grow past today's when farming pays more. Rule: farm_intake.kept_farm_workers on built inputs. The bounds (satiation, land,
no price) are in test_farm_satiation; the farm's hours in a game are test_farm_effort_follows_price."""
QUICK_TOPIC = True

import unittest

from sim.labour import farm_intake

ELASTICITY = 0.5


def kept(ratio, satiation=100.0, land=100.0, current=10.0):
	return farm_intake.kept_farm_workers(current, satiation, land, ratio, ELASTICITY)


class HandsAtTheMarginRuleTests(unittest.TestCase):
	def test_hands_stay_where_the_farm_hour_pays_the_wage_exactly(self):
		self.assertAlmostEqual(kept(1.0), 10.0)

	def test_hands_do_not_join_past_today_when_farming_pays_more_than_the_wage(self):
		self.assertAlmostEqual(kept(3.0), 10.0)

	def test_hands_fall_continuously_with_the_value_of_a_farm_hour(self):
		ratios = [0.5, 0.7, 0.8, 0.9, 1.0]
		values = [kept(ratio) for ratio in ratios]
		self.assertEqual(values, sorted(values))
		self.assertEqual(len(set(values)), len(values))
		for lower, higher in zip(values, values[1:]):
			self.assertLess(higher - lower, 0.6 * higher)

	def test_a_farm_hour_worth_less_than_the_wage_lets_hands_go(self):
		self.assertLess(kept(0.5), 10.0)

	def test_hands_never_exceed_satiation_or_the_cleared_land(self):
		self.assertAlmostEqual(kept(50.0, satiation=8.0), 8.0)
		self.assertAlmostEqual(kept(50.0, land=6.0), 6.0)


if __name__ == "__main__":
	unittest.main()
