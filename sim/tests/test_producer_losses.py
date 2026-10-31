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


class CloseYearTests(unittest.TestCase):
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
        ledger.note_rent([Transfer("producer:a", "cohort:b", "gold", 30.0, "rent")])
        self.assertAlmostEqual(ledger.running_costs("producer:a"), 30.0)
        self.assertEqual(ledger.running_costs("cohort:b"), 0.0)


if __name__ == "__main__":
    unittest.main()
