"""plot_hours_value: what an hour on the family plot grows, and the return figure under which the hours schedule keeps
every hour the plot takes while the crop is worth more than the wage."""

QUICK_TOPIC = True

import unittest

from sim.economy.households_hours_offered import plot_hours_kept
from sim.economy.labour_ask_floor import plot_return_per_hour
from sim.economy.plot_hours_value import (crop_value_per_hour, return_keeping_what_the_plot_grows, return_of_the_next_hour,
                                          return_that_keeps_the_usable_hours)
from sim.world.need_basket import NeedSpec, PricedNeed

FOOD = PricedNeed(NeedSpec("food", 10.0, 1.0, (("grain", 1.0),)), 2.0, (("grain", 2.0, 1.0, 1.0),))
WARMTH = PricedNeed(NeedSpec("warmth", 100.0, 1.0, (("wood", 1.0),)), 0.1, (("wood", 0.1, 1.0, 1.0),))
CLOTH = PricedNeed(NeedSpec("cloth", 1.0, 1.0, (("linen", 1.0),)), 30.0, (("linen", 30.0, 1.0, 1.0),))
OPTIONS = {"food": [(5.0, "grow_grain", "grain", 1.0)],        # five hours a need unit at fertility one
           "warmth": [(0.2, "cut_wood", "wood", 1.0)]}
HECTARES = {"grow_grain": 0.01, "cut_wood": 0.001}
YEAR, USABLE = 2000.0, 300.0


class CropValuePerHour(unittest.TestCase):
    def test_the_worth_of_a_need_unit_over_the_hours_it_takes(self):
        self.assertAlmostEqual(crop_value_per_hour([FOOD, CLOTH], OPTIONS, 1.0), 2.0 / 5.0)

    def test_several_needs_weigh_by_the_hours_their_floors_take(self):
        # food: ten units worth two each over fifty hours; warmth: a hundred units worth a tenth each over twenty hours
        self.assertAlmostEqual(crop_value_per_hour([FOOD, WARMTH], OPTIONS, 1.0), (10.0 * 2.0 + 100.0 * 0.1) / (50.0 + 20.0))

    def test_poor_soil_takes_more_hours_for_the_same_crop(self):
        self.assertAlmostEqual(crop_value_per_hour([FOOD], OPTIONS, 0.5), 0.5 * 2.0 / 5.0)

    def test_the_states_share_of_the_harvest_is_not_the_households(self):
        self.assertAlmostEqual(crop_value_per_hour([FOOD], OPTIONS, 1.0, {"grain": 0.2}), 0.8 * 2.0 / 5.0)

    def test_nothing_where_the_plot_grows_none_of_the_needs_or_the_soil_grows_nothing(self):
        self.assertEqual(crop_value_per_hour([CLOTH], OPTIONS, 1.0), 0.0)
        self.assertEqual(crop_value_per_hour([FOOD], OPTIONS, 0.0), 0.0)
        self.assertEqual(crop_value_per_hour([], OPTIONS, 1.0), 0.0)


class ReturnThatKeepsTheUsableHours(unittest.TestCase):
    def kept(self, wage, crop_value=0.4):
        return plot_hours_kept(YEAR, wage, return_that_keeps_the_usable_hours(crop_value, USABLE, YEAR), USABLE)

    def test_every_usable_hour_is_kept_while_the_crop_is_worth_the_wage_or_more(self):
        for wage in (0.1, 0.3, 0.4):
            self.assertAlmostEqual(self.kept(wage), USABLE)

    def test_fewer_are_kept_as_the_wage_rises_above_the_crops_worth_and_never_none(self):
        self.assertAlmostEqual(self.kept(0.8), USABLE * (0.4 / 0.8) ** 2.0)
        self.assertLess(self.kept(1.6), self.kept(0.8))
        self.assertGreater(self.kept(1.6), 0.0)

    def test_the_hours_kept_do_not_jump_as_the_wage_crosses_the_crops_worth(self):
        self.assertAlmostEqual(self.kept(0.4 * (1.0 + 1e-9)), USABLE, places=4)

    def test_a_dearer_crop_keeps_the_hours_up_to_a_higher_wage(self):
        self.assertAlmostEqual(self.kept(0.8, crop_value=0.8), USABLE)

    def test_nothing_to_keep_gives_no_return(self):
        self.assertEqual(return_that_keeps_the_usable_hours(0.4, 0.0, YEAR), 0.0)
        self.assertEqual(return_that_keeps_the_usable_hours(0.4, USABLE, 0.0), 0.0)
        self.assertEqual(return_that_keeps_the_usable_hours(0.0, USABLE, YEAR), 0.0)

    def test_a_plot_that_takes_more_than_the_year_keeps_the_year(self):
        self.assertAlmostEqual(plot_hours_kept(YEAR, 0.3, return_that_keeps_the_usable_hours(0.4, 5000.0, YEAR), 5000.0), YEAR)


class TheTwoRules(unittest.TestCase):
    ARGUMENTS = ([FOOD], OPTIONS, 1.0, YEAR, 2.0, HECTARES, 0.05, None)

    def test_the_next_hours_return_is_the_ask_floors_and_ignores_the_usable_hours(self):
        self.assertEqual(return_of_the_next_hour(*self.ARGUMENTS, USABLE), plot_return_per_hour(*self.ARGUMENTS))

    def test_keeping_what_the_plot_grows_reads_the_crops_worth_and_the_usable_hours(self):
        self.assertAlmostEqual(return_keeping_what_the_plot_grows(*self.ARGUMENTS, USABLE),
                               return_that_keeps_the_usable_hours(2.0 / 5.0, USABLE, YEAR))


if __name__ == "__main__":
    unittest.main()
