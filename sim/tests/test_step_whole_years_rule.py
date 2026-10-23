"""A step is a whole number of years: 0.999 and 1.99 are both refused, neither rounded to a year nor floored. Rule: the
`step` command's years check, called with a stand-in game (the check runs before the game is read). The play of a
legitimate step is in the scenarios."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.ui.proto.dispatch import _cmd_step

GAME = SimpleNamespace(year=100, end_year=200)


def step(years):
	return _cmd_step(GAME, {}, {"cmd": "step", "years": years}, None)


class StepWholeYearsTests(unittest.TestCase):
	def test_a_fraction_of_a_year_is_refused_on_either_side_of_one(self):
		for years in (0.999, 1.01, 1.99):
			self.assertIs(step(years)["ok"], False, years)

	def test_a_truth_value_is_not_a_number_of_years(self):
		self.assertIs(step(True)["ok"], False)

	def test_zero_and_negative_years_are_refused(self):
		for years in (0, -3):
			self.assertIs(step(years)["ok"], False, years)

	def test_more_years_than_the_game_has_left_are_refused(self):
		self.assertIs(step(101)["ok"], False)


if __name__ == "__main__":
	unittest.main()
