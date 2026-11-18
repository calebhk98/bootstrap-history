"""A producer whose realised cash flow after every cost (wages, inputs, rent, interest, plant wear) is negative cuts
capacity in proportion to the loss. Each test calls one function with written-out inputs."""

QUICK_TOPIC = True

import unittest

from sim.economy import producer_losses, producers_close
from sim.economy.producers import OUTPUT_CHANGE_SHARE_PER_YEAR
from sim.economy.year_ledger import YearLedger
from sim.economy.types import Transfer
from sim.tests.test_economy_producers import FARM, farm_view, farmer


class ShedShareTests(unittest.TestCase):
    def test_a_loss_sheds_the_share_of_its_outlay_revenue_did_not_cover(self):
        # revenue 90 against an outlay of 100: earnings -10, a tenth of the outlay
        self.assertAlmostEqual(producer_losses.shed_share((-10.0,), (90.0,)), 0.1)

    def test_a_profit_sheds_nothing(self):
        self.assertEqual(producer_losses.shed_share((20.0,), (120.0,)), 0.0)

    def test_a_loss_larger_than_the_yearly_pace_sheds_the_pace(self):
        self.assertAlmostEqual(producer_losses.shed_share((-80.0,), (20.0,)), OUTPUT_CHANGE_SHARE_PER_YEAR)

    def test_the_remembered_years_are_averaged(self):
        # earnings -10 and +10 average to nothing
        self.assertEqual(producer_losses.shed_share((-10.0, 10.0), (90.0, 110.0)), 0.0)

    def test_a_small_loss_sheds_in_proportion(self):
        self.assertAlmostEqual(producer_losses.shed_share((-1.0,), (99.0,)), 0.01)

    def test_no_history_sheds_nothing(self):
        self.assertEqual(producer_losses.shed_share((), ()), 0.0)

    def test_no_revenue_and_no_cost_sheds_nothing(self):
        self.assertEqual(producer_losses.shed_share((0.0,), (0.0,)), 0.0)


class CapacityAfterLossesTests(unittest.TestCase):
    def test_a_loss_closes_its_share_where_sales_call_for_fewer_workplaces_than_are_left(self):
        # ten workplaces, a fifth to close; sales of three runs with six tenths of workplaces paying call for five
        self.assertAlmostEqual(producer_losses.capacity_after_losses(10.0, 0.2, 3.0, 0.6), 8.0)

    def test_a_loss_closes_no_workplace_its_expected_sales_still_call_for(self):
        # sales of nine runs with six tenths paying call for fifteen workplaces: all ten stay
        self.assertAlmostEqual(producer_losses.capacity_after_losses(10.0, 0.2, 9.0, 0.6), 10.0)

    def test_a_loss_closes_down_to_the_workplaces_sales_call_for_and_no_further(self):
        # a quarter to close would leave seven and a half; sales of 5.4 runs call for nine
        self.assertAlmostEqual(producer_losses.capacity_after_losses(10.0, 0.25, 5.4, 0.6), 9.0)

    def test_with_no_sales_expected_the_loss_closes_its_share(self):
        self.assertAlmostEqual(producer_losses.capacity_after_losses(10.0, 0.2, 0.0, 0.6), 8.0)

    def test_where_no_workplace_pays_the_loss_closes_its_share(self):
        self.assertAlmostEqual(producer_losses.capacity_after_losses(10.0, 0.2, 9.0, 0.0), 8.0)

    def test_no_loss_leaves_the_capacity(self):
        self.assertAlmostEqual(producer_losses.capacity_after_losses(10.0, 0.0, 1.0, 0.6), 10.0)


class CloseYearTests(unittest.TestCase):
    def test_a_producer_losing_cash_while_its_sales_call_for_all_its_workplaces_closes_none(self):
        # the same loss as below, but it expects to sell twelve runs, more than its ten workplaces make
        result = producers_close.close_year(farmer(capacity_runs=10.0, expected_sales=12.0), FARM, 80.0, 100.0, farm_view(2.0), 5.0)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0)

    def test_the_runs_buyers_called_for_this_year_count_in_the_sales_that_keep_workplaces(self):
        # it expected two runs; buyers called for forty: the sales it will expect call for more than its ten workplaces
        result = producers_close.close_year(farmer(capacity_runs=10.0, expected_sales=2.0), FARM, 80.0, 100.0, farm_view(2.0), 5.0,
                                            demand_runs=40.0)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0)

    def test_a_producer_expecting_a_margin_but_losing_cash_sheds_in_proportion_to_the_loss(self):
        # expected prices pay (farm_view(2.0)); the year's revenue fell a fifth short of what it paid out
        result = producers_close.close_year(farmer(capacity_runs=10.0), FARM, 80.0, 100.0, farm_view(2.0), 5.0)
        self.assertFalse(result.exited)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0 * (1.0 - 20.0 / 100.0))

    def test_interest_paid_counts_in_the_loss(self):
        result = producers_close.close_year(farmer(capacity_runs=10.0), FARM, 100.0, 100.0, farm_view(2.0), 5.0, interest=10.0)
        self.assertAlmostEqual(result.producer.capacity_runs, 10.0 * (1.0 - 10.0 / 110.0))


class RentInRunningCostsTests(unittest.TestCase):
    def test_rent_paid_counts_in_the_payer_running_costs(self):
        ledger = YearLedger()
        ledger.note_paid_outside_markets([Transfer("producer:a", "cohort:b", "gold", 30.0, "rent")])
        self.assertAlmostEqual(ledger.running_costs("producer:a"), 30.0)
        self.assertEqual(ledger.running_costs("cohort:b"), 0.0)


if __name__ == "__main__":
    unittest.main()
