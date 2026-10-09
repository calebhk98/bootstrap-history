"""The lowest a worker's ask falls to is what the family's plot gives it without a wage."""

QUICK_TOPIC = True

import unittest

from sim.economy.labour_ask_floor import plot_value_per_worker_year
from sim.world.need_basket import NeedSpec, PricedNeed

FOOD = PricedNeed(NeedSpec("food", 10.0, 1.0, (("grain", 1.0),)), 2.0, (("grain", 2.0, 1.0, 1.0),))
CLOTH = PricedNeed(NeedSpec("cloth", 1.0, 1.0, (("linen", 1.0),)), 30.0, (("linen", 30.0, 1.0, 1.0),))
OPTIONS = {"food": [(5.0, "grow_grain", "grain", 1.0)]}       # five hours a need unit at fertility one


class PlotValueTests(unittest.TestCase):
    def test_a_plot_that_fits_the_workers_year_is_worth_the_floors_it_grows(self):
        # a person's food floor is ten units worth twenty, fifty hours; a worker feeds two people
        self.assertAlmostEqual(plot_value_per_worker_year([FOOD, CLOTH], OPTIONS, 1.0, 1000.0, 2.0), 40.0)

    def test_a_year_too_short_for_the_plot_limits_the_value(self):
        self.assertAlmostEqual(plot_value_per_worker_year([FOOD], OPTIONS, 1.0, 40.0, 2.0), 16.0)

    def test_poor_soil_takes_more_hours_so_the_year_buys_less(self):
        self.assertAlmostEqual(plot_value_per_worker_year([FOOD], OPTIONS, 0.5, 40.0, 2.0), 8.0)

    def test_a_family_with_no_plot_option_has_nothing_without_a_wage(self):
        self.assertEqual(plot_value_per_worker_year([CLOTH], OPTIONS, 1.0, 1000.0, 2.0), 0.0)
        self.assertEqual(plot_value_per_worker_year([FOOD], OPTIONS, 0.0, 1000.0, 2.0), 0.0)


if __name__ == "__main__":
    unittest.main()
