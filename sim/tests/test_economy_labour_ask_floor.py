"""The lowest a worker's ask falls to is what keeping the household alive costs, less what its plot gives."""

QUICK_TOPIC = True

import unittest

from sim.economy.labour_ask_floor import mean_floor_per_hour, plot_value_per_worker_year, wage_floor_per_worker_year
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


class WageFloorTests(unittest.TestCase):
    def test_the_floor_is_the_basket_less_the_plot(self):
        # two people at ten food units (twenty) and one cloth unit (thirty) each cost a hundred; the plot grows forty
        self.assertAlmostEqual(wage_floor_per_worker_year([FOOD, CLOTH], OPTIONS, 1.0, 1000.0, 2.0), 60.0)

    def test_a_family_with_no_plot_needs_the_whole_basket_from_wages(self):
        self.assertAlmostEqual(wage_floor_per_worker_year([FOOD, CLOTH], OPTIONS, 0.0, 1000.0, 2.0), 100.0)
        self.assertAlmostEqual(wage_floor_per_worker_year([CLOTH], OPTIONS, 1.0, 1000.0, 2.0), 60.0)

    def test_a_plot_that_feeds_everything_needed_leaves_no_floor(self):
        self.assertEqual(wage_floor_per_worker_year([FOOD], OPTIONS, 1.0, 1000.0, 2.0), 0.0)

    def test_dearer_goods_raise_the_floor(self):
        dear = PricedNeed(CLOTH.spec, 60.0, (("linen", 60.0, 1.0, 1.0),))
        self.assertGreater(wage_floor_per_worker_year([FOOD, dear], OPTIONS, 1.0, 1000.0, 2.0),
                           wage_floor_per_worker_year([FOOD, CLOTH], OPTIONS, 1.0, 1000.0, 2.0))

    def test_no_basket_priced_means_no_floor(self):
        self.assertEqual(wage_floor_per_worker_year([], OPTIONS, 1.0, 1000.0, 2.0), 0.0)


class MeanFloorTests(unittest.TestCase):
    def test_areas_weigh_by_their_workers_and_the_year_is_split_into_hours(self):
        floors = {"a": 100.0, "b": 400.0}
        self.assertAlmostEqual(mean_floor_per_hour(floors, {"a": 3.0, "b": 1.0}, 100.0), 1.75)

    def test_no_workers_or_no_hours_means_no_floor(self):
        self.assertEqual(mean_floor_per_hour({"a": 100.0}, {}, 100.0), 0.0)
        self.assertEqual(mean_floor_per_hour({"a": 100.0}, {"a": 1.0}, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
