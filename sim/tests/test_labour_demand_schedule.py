"""labour_demand: the cost multiple of a share of a producer's workplaces, the worth of each slice, the most runs wanted."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy.labour_demand import cost_multiple_at, most_runs_wanted, runs_held_back_for_stock, slice_worths
from sim.economy.producers import OUTPUT_CHANGE_SHARE_PER_YEAR, Producer, share_working


def make_producer(capacity_runs, **changes):
    return Producer("producer:a", "owner:a", "boil_salt", "tile:a", capacity_runs, **changes)


class CostMultipleAt(unittest.TestCase):
    def test_it_inverts_the_share_of_workplaces_a_revenue_covers(self):
        for revenue, cost in ((7.0, 10.0), (10.0, 10.0), (15.0, 10.0)):
            share = share_working(revenue, cost)
            self.assertAlmostEqual(cost * cost_multiple_at(share), revenue, places=6)

    def test_the_multiple_rises_with_the_share(self):
        self.assertLess(cost_multiple_at(0.25), cost_multiple_at(0.5))
        self.assertLess(cost_multiple_at(0.5), cost_multiple_at(0.75))


class SliceWorths(unittest.TestCase):
    def test_runs_sum_to_the_smaller_of_capacity_and_most_runs(self):
        for capacity, most in ((10.0, 8.0), (10.0, 20.0)):
            worths = slice_worths(capacity, most, 10.0, 1.0, slices=4)
            self.assertEqual(len(worths), 4)
            self.assertAlmostEqual(sum(runs for runs, _room in worths), min(capacity, most))

    def test_worths_fall_from_the_first_slice_to_the_last(self):
        rooms = [room for _runs, room in slice_worths(10.0, 8.0, 10.0, 1.0, slices=4)]
        self.assertTrue(rooms[0] > rooms[1] > rooms[2] > rooms[3])

    def test_a_slice_that_leaves_nothing_and_every_later_one_are_left_out(self):
        # revenue 10 against other costs of 9.5: the slice at share 0.75 costs 1.17 times the middle, leaving 10 / 1.17 - 9.5 < 0
        worths = slice_worths(8.0, 8.0, 10.0, 9.5, slices=4)
        self.assertEqual(len(worths), 3)
        self.assertTrue(all(room > 0.0 for _runs, room in worths))

    def test_nothing_comes_of_no_capacity_no_runs_or_no_revenue(self):
        self.assertEqual(slice_worths(0.0, 5.0, 10.0, 1.0), [])
        self.assertEqual(slice_worths(10.0, 0.0, 10.0, 1.0), [])
        self.assertEqual(slice_worths(10.0, 5.0, 0.0, 1.0), [])


def runs_wanted_at(worths, hours_cost):
    """Runs of the slices whose run leaves at least `hours_cost` for its hours."""
    return sum(runs for runs, room in worths if room >= hours_cost)


class SliceWorthsWithRunsHeldBack(unittest.TestCase):
    CAPACITY, MOST, REVENUE, OTHER = 100.0, 80.0, 10.0, 1.0

    def test_the_runs_sum_to_most_runs_less_the_runs_held_back(self):
        worths = slice_worths(self.CAPACITY, self.MOST, self.REVENUE, self.OTHER, slices=8, runs_held_back=20.0)
        self.assertAlmostEqual(sum(runs for runs, _room in worths), self.MOST - 20.0)

    def test_the_dearest_slice_is_worth_what_it_is_with_nothing_held_back(self):
        # the last slice's cheapest workplace sits at the same run with and without the overhang when the slices line up
        bare = slice_worths(self.CAPACITY, self.MOST, self.REVENUE, self.OTHER, slices=8)
        held = slice_worths(self.CAPACITY, self.MOST, self.REVENUE, self.OTHER, slices=6, runs_held_back=20.0)
        self.assertAlmostEqual(held[-1][1], bare[-1][1])
        self.assertAlmostEqual(held[0][1], bare[2][1])

    def test_at_a_wage_the_runs_wanted_are_the_runs_that_pay_less_the_runs_held_back(self):
        bare = slice_worths(self.CAPACITY, self.MOST, self.REVENUE, self.OTHER, slices=8)
        held = slice_worths(self.CAPACITY, self.MOST, self.REVENUE, self.OTHER, slices=6, runs_held_back=20.0)
        for hours_cost in (bare[3][1], bare[5][1], bare[7][1]):
            self.assertAlmostEqual(runs_wanted_at(held, hours_cost), runs_wanted_at(bare, hours_cost) - 20.0)

    def test_everything_held_back_leaves_no_bid(self):
        self.assertEqual(slice_worths(self.CAPACITY, self.MOST, self.REVENUE, self.OTHER, runs_held_back=80.0), [])
        self.assertEqual(slice_worths(self.CAPACITY, self.MOST, self.REVENUE, self.OTHER, runs_held_back=95.0), [])

    def test_a_negative_figure_holds_nothing_back(self):
        self.assertEqual(slice_worths(self.CAPACITY, self.MOST, self.REVENUE, self.OTHER, runs_held_back=-5.0),
                         slice_worths(self.CAPACITY, self.MOST, self.REVENUE, self.OTHER))


class RunsHeldBackForStock(unittest.TestCase):
    def test_the_runs_that_pay_less_the_runs_the_stock_calls_for(self):
        self.assertAlmostEqual(runs_held_back_for_stock(50.0, 35.0), 15.0)

    def test_none_where_the_stock_calls_for_as_many_or_more(self):
        self.assertEqual(runs_held_back_for_stock(50.0, 50.0), 0.0)
        self.assertEqual(runs_held_back_for_stock(50.0, 70.0), 0.0)

    def test_none_with_no_record_to_read_the_stock_against(self):
        self.assertEqual(runs_held_back_for_stock(50.0, math.inf), 0.0)


class MostRunsWanted(unittest.TestCase):
    def test_capacity_binds(self):
        producer = make_producer(4.0)       # no last year: the growth ceiling is the capacity
        self.assertAlmostEqual(most_runs_wanted(producer, 1000.0, 10.0, 0.0), 4.0)

    def test_the_growth_ceiling_binds(self):
        producer = make_producer(10.0, last_runs=2.0, expected_sales=0.0)
        self.assertAlmostEqual(most_runs_wanted(producer, 1000.0, 10.0, 0.0), 2.0 + OUTPUT_CHANGE_SHARE_PER_YEAR * 10.0)

    def test_cash_and_held_inputs_over_the_price_paid_now_bind(self):
        producer = make_producer(10.0)
        self.assertAlmostEqual(most_runs_wanted(producer, 30.0, 10.0, 5.0), (30.0 + 5.0) / 10.0)

    def test_negative_cash_counts_as_none(self):
        self.assertAlmostEqual(most_runs_wanted(make_producer(10.0), -50.0, 5.0, 10.0), 10.0 / 5.0)

    def test_nothing_paid_now_leaves_cash_out_of_it(self):
        self.assertAlmostEqual(most_runs_wanted(make_producer(10.0), 0.0, 0.0, 0.0), 10.0)

    def test_the_runs_its_inputs_allow_bind(self):
        producer = make_producer(10.0)
        self.assertAlmostEqual(most_runs_wanted(producer, 1000.0, 10.0, 0.0, runs_its_inputs_allow=3.0), 3.0)

    def test_no_figure_for_its_inputs_leaves_them_out_of_it(self):
        self.assertAlmostEqual(most_runs_wanted(make_producer(10.0), 1000.0, 10.0, 0.0), 10.0)

    def test_the_land_binds(self):
        producer = make_producer(10.0, land_run_cap=2.0)
        self.assertAlmostEqual(most_runs_wanted(producer, 1000.0, 10.0, 0.0), 2.0)


if __name__ == "__main__":
    unittest.main()
