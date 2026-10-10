"""The lowest a worker's ask falls to is what an hour is worth on the household's own plot."""

QUICK_TOPIC = True

import unittest

from sim.economy.labour_ask_floor import (mean_floor_per_hour, plot_return_per_hour, plot_value_per_worker_year,
                                      survival_cost_per_worker_year, wage_floor_per_worker_year)
from sim.world.need_basket import NeedSpec, PricedNeed

FOOD = PricedNeed(NeedSpec("food", 10.0, 1.0, (("grain", 1.0),)), 2.0, (("grain", 2.0, 1.0, 1.0),))
CLOTH = PricedNeed(NeedSpec("cloth", 1.0, 1.0, (("linen", 1.0),)), 30.0, (("linen", 30.0, 1.0, 1.0),))
OPTIONS = {"food": [(5.0, "grow_grain", "grain", 1.0)]}       # five hours a need unit at fertility one
HECTARES = {"grow_grain": 0.01}                               # a hundred hours work a hectare, so twenty units a hectare


def marginal(price, fertility, hours, people):
    """The closed form for the fixture: a plot of people * ten units at twenty units a hectare."""
    plot = people * 10.0 / 20.0
    hours_per_hectare = hours / plot
    reference_hours = 1.0 / (fertility * 0.01)
    return price * 0.5 * 20.0 * (hours_per_hectare / reference_hours) ** 0.5 / hours_per_hectare


class PlotReturnTests(unittest.TestCase):
    def test_the_next_hour_adds_the_labour_elasticity_share_of_output_per_hour_on_the_plot(self):
        self.assertAlmostEqual(plot_return_per_hour([FOOD, CLOTH], OPTIONS, 1.0, 1000.0, 2.0, HECTARES),
                               marginal(2.0, 1.0, 1000.0, 2.0))

    def test_more_hours_on_the_same_land_add_less_each(self):
        self.assertLess(plot_return_per_hour([FOOD], OPTIONS, 1.0, 4000.0, 2.0, HECTARES),
                        plot_return_per_hour([FOOD], OPTIONS, 1.0, 1000.0, 2.0, HECTARES))

    def test_a_bigger_family_has_more_land_per_hour_so_an_hour_adds_more(self):
        self.assertGreater(plot_return_per_hour([FOOD], OPTIONS, 1.0, 1000.0, 4.0, HECTARES),
                           plot_return_per_hour([FOOD], OPTIONS, 1.0, 1000.0, 2.0, HECTARES))

    def test_poor_soil_adds_less(self):
        self.assertAlmostEqual(plot_return_per_hour([FOOD], OPTIONS, 0.5, 1000.0, 2.0, HECTARES),
                               marginal(2.0, 0.5, 1000.0, 2.0))

    def test_dearer_output_raises_the_return(self):
        dear = PricedNeed(FOOD.spec, 4.0, (("grain", 4.0, 1.0, 1.0),))
        self.assertAlmostEqual(plot_return_per_hour([dear], OPTIONS, 1.0, 1000.0, 2.0, HECTARES),
                               2.0 * plot_return_per_hour([FOOD], OPTIONS, 1.0, 1000.0, 2.0, HECTARES))

    def test_no_plot_option_or_no_land_or_no_hours_means_no_alternative(self):
        self.assertEqual(plot_return_per_hour([CLOTH], OPTIONS, 1.0, 1000.0, 2.0, HECTARES), 0.0)
        self.assertEqual(plot_return_per_hour([FOOD], OPTIONS, 0.0, 1000.0, 2.0, HECTARES), 0.0)
        self.assertEqual(plot_return_per_hour([FOOD], OPTIONS, 1.0, 0.0, 2.0, HECTARES), 0.0)
        self.assertEqual(plot_return_per_hour([FOOD], OPTIONS, 1.0, 1000.0, 2.0, {}), 0.0)
        self.assertEqual(plot_return_per_hour([], OPTIONS, 1.0, 1000.0, 2.0, HECTARES), 0.0)


class SurvivalCostTests(unittest.TestCase):
    def test_the_cost_is_the_basket_less_what_the_plot_grows(self):
        # two people at ten food units (twenty) and one cloth unit (thirty) each cost a hundred; the plot grows forty
        self.assertAlmostEqual(plot_value_per_worker_year([FOOD, CLOTH], OPTIONS, 1.0, 1000.0, 2.0), 40.0)
        self.assertAlmostEqual(survival_cost_per_worker_year([FOOD, CLOTH], OPTIONS, 1.0, 1000.0, 2.0), 60.0)

    def test_a_family_with_no_plot_needs_the_whole_basket_from_wages(self):
        self.assertAlmostEqual(survival_cost_per_worker_year([FOOD, CLOTH], OPTIONS, 0.0, 1000.0, 2.0), 100.0)

    def test_a_plot_that_feeds_everything_needed_leaves_no_cost(self):
        self.assertEqual(survival_cost_per_worker_year([FOOD], OPTIONS, 1.0, 1000.0, 2.0), 0.0)


class WageFloorTests(unittest.TestCase):
    def test_a_family_with_no_plot_cannot_go_below_what_keeps_it_fed(self):
        self.assertAlmostEqual(wage_floor_per_worker_year([FOOD, CLOTH], OPTIONS, 0.0, 1000.0, 2.0, HECTARES), 100.0)

    def test_the_floor_is_a_years_hours_at_the_plot_return(self):
        self.assertAlmostEqual(wage_floor_per_worker_year([FOOD, CLOTH], OPTIONS, 1.0, 1000.0, 2.0, HECTARES),
                               1000.0 * marginal(2.0, 1.0, 1000.0, 2.0))

    def test_no_basket_priced_means_no_floor(self):
        self.assertEqual(wage_floor_per_worker_year([], OPTIONS, 1.0, 1000.0, 2.0, HECTARES), 0.0)


class MeanFloorTests(unittest.TestCase):
    def test_areas_weigh_by_their_workers_and_the_year_is_split_into_hours(self):
        floors = {"a": 100.0, "b": 400.0}
        self.assertAlmostEqual(mean_floor_per_hour(floors, {"a": 3.0, "b": 1.0}, 100.0), 1.75)

    def test_no_workers_or_no_hours_means_no_floor(self):
        self.assertEqual(mean_floor_per_hour({"a": 100.0}, {}, 100.0), 0.0)
        self.assertEqual(mean_floor_per_hour({"a": 100.0}, {"a": 1.0}, 0.0), 0.0)


class AskSlideTests(unittest.TestCase):
    def test_unsold_years_never_slide_the_ask_below_what_an_hour_on_the_plot_earns(self):
        from sim.labour.market import asks
        from sim.labour.market.records import MarketState
        hours_per_year = 1000.0
        floor = wage_floor_per_worker_year([FOOD, CLOTH], OPTIONS, 1.0, hours_per_year, 2.0, HECTARES) / hours_per_year
        plot_hour = marginal(2.0, 1.0, hours_per_year, 2.0)                 # what the next hour grows, at its price
        reservation = 1.0
        state = MarketState()
        for _year in range(30):
            asks.record(state, "vale", "labourer", 100.0, 0.0, 0.0, reservation, lowest=floor)
        self.assertGreaterEqual(asks.scale_of(state, "vale", "labourer") * reservation, plot_hour - 1e-9)


if __name__ == "__main__":
    unittest.main()
