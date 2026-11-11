"""Complaint 657: the fiscal menu nets the unrest a take arms. Each test writes out the inputs and calls one rule."""
import math
import unittest

from sim.agents import fiscal_unrest, unrest

QUICK_TOPIC = True


class UnrestAdded(unittest.TestCase):
	def test_it_is_the_unrest_rule_of_the_grievance_the_extra_take_makes(self):
		self.assertAlmostEqual(fiscal_unrest.unrest_added(100.0, 1000.0), 1.0 - math.exp(-0.1))
		self.assertEqual(fiscal_unrest.unrest_added(100.0, 1000.0), unrest.unrest(unrest.grievance(100.0, 0.0, 0.0, 1000.0), None, 0.0))

	def test_no_income_to_take_from_arms_no_unrest(self):
		self.assertEqual(fiscal_unrest.unrest_added(100.0, 0.0), 0.0)

	def test_a_bigger_take_arms_more(self):
		self.assertGreater(fiscal_unrest.unrest_added(300.0, 1000.0), fiscal_unrest.unrest_added(100.0, 1000.0))


class NetOfUnrest(unittest.TestCase):
	def test_the_discontented_do_not_pay(self):
		self.assertAlmostEqual(fiscal_unrest.net_of_unrest(100.0, 1000.0), 100.0 * math.exp(-0.1))

	def test_it_is_never_more_than_taken_nor_below_nothing(self):
		self.assertLess(fiscal_unrest.net_of_unrest(100.0, 1000.0), 100.0)
		self.assertEqual(fiscal_unrest.net_of_unrest(-5.0, 1000.0), 0.0)

	def test_the_same_raise_on_a_poorer_base_yields_less(self):
		self.assertLess(fiscal_unrest.net_of_unrest(100.0, 500.0), fiscal_unrest.net_of_unrest(100.0, 5000.0))

	def test_no_visible_income_leaves_the_take_whole(self):
		self.assertEqual(fiscal_unrest.net_of_unrest(100.0, 0.0), 100.0)


class LostPerMoneyKept(unittest.TestCase):
	def test_it_is_the_loss_over_the_money_kept(self):
		self.assertAlmostEqual(fiscal_unrest.lost_per_money_kept(100.0, 1000.0), math.exp(0.1) - 1.0)

	def test_nothing_taken_loses_nothing(self):
		self.assertEqual(fiscal_unrest.lost_per_money_kept(0.0, 1000.0), 0.0)
