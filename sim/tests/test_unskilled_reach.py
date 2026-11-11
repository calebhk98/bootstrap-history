"""Complaint 965: a thin unskilled market's wage is an option only for the hours its jobs can take, so it no longer sets
every skilled trade's reservation. Rules called on values written out here."""
QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing, trades
from sim.labour.market.records import EmployerHoursBid, MarketState, YearInputs
from sim.labour.market.unskilled_reach import reservation_with_unskilled_option, share_reaching_unskilled

SPECS = trades.trade_specs({"digger": {"family": "earth", "training_years": 0},
                            "farmer": {"family": "earth", "training_years": 1}})


class ShareOfHours(unittest.TestCase):
    def test_jobs_for_every_hour_of_the_trade_take_all_of_it_and_no_more(self):
        self.assertEqual(share_reaching_unskilled(2000.0, 1000.0), 1.0)
        self.assertEqual(share_reaching_unskilled(1000.0, 1000.0), 1.0)

    def test_a_few_jobs_take_a_few_hours_in_proportion(self):
        self.assertAlmostEqual(share_reaching_unskilled(50.0, 1000.0), 0.05)
        self.assertEqual(share_reaching_unskilled(0.0, 1000.0), 0.0)

    def test_a_trade_with_no_hours_has_nothing_the_option_could_move(self):
        self.assertEqual(share_reaching_unskilled(0.0, 0.0), 1.0)


class Reservation(unittest.TestCase):
    def test_a_thin_unskilled_market_leaves_the_trade_near_its_own_reservation(self):
        self.assertAlmostEqual(reservation_with_unskilled_option(1.0, 10.0, 5.0, 1000.0), 1.0 + 0.005 * 9.0)

    def test_a_deep_unskilled_market_sets_the_whole_option(self):
        self.assertEqual(reservation_with_unskilled_option(1.0, 10.0, 5000.0, 1000.0), 10.0)

    def test_the_reservation_rises_continuously_with_the_jobs(self):
        steps = [reservation_with_unskilled_option(1.0, 10.0, jobs, 1000.0) for jobs in (0.0, 100.0, 500.0, 999.0, 1000.0, 3000.0)]
        self.assertEqual(steps, sorted(steps))
        self.assertAlmostEqual(steps[3], steps[4], delta=0.02)

    def test_no_option_or_a_lower_one_leaves_the_own_reservation(self):
        self.assertEqual(reservation_with_unskilled_option(1.0, None, 5000.0, 1000.0), 1.0)
        self.assertEqual(reservation_with_unskilled_option(4.0, 2.0, 5000.0, 1000.0), 4.0)


class ThinUnskilledMarket(unittest.TestCase):
    def _year(self, unskilled_job_hours):
        inputs = YearInputs(trades=SPECS, subsistence_per_worker_year={"vale": 100.0}, hours_per_worker_year=100.0,
                            discount_rate=0.03, career_years=30.0,
                            bids=[EmployerHoursBid("mill", "digger", "vale", unskilled_job_hours, 9.0),
                                  EmployerHoursBid("farm", "farmer", "vale", 800.0, 2.0)])
        state = MarketState(workers={"vale": {"digger": [1.0, 0, 0, 0, 0], "farmer": [10.0, 0, 0, 0, 0]}})
        state.wages = {"vale": {"digger": 8.0, "farmer": 1.0}}       # the thin market paid 8 against a farm wage of 1
        return inputs, state

    def _farm_wage_and_hours(self, unskilled_job_hours):
        inputs, state = self._year(unskilled_job_hours)
        results = {each.trade: each for each in clearing.clear_all(state, inputs)}
        return results["farmer"].wage, results["farmer"].hours_hired

    def test_the_plain_rule_and_the_packed_kernel_give_the_farm_the_same_wage(self):
        for jobs in (20.0, 300.0, 5000.0):
            inputs, state = self._year(jobs)
            packed = {each.trade: each for each in clearing.clear_all(state, inputs)}["farmer"].wage
            inputs, state = self._year(jobs)
            plain = clearing.clear_one(state, inputs, "farmer", "vale", [bid for bid in inputs.bids if bid.trade == "farmer"]).wage
            self.assertAlmostEqual(packed, plain, places=9)

    def test_a_thin_unskilled_market_does_not_stop_the_farm_hiring(self):
        wage, hired = self._farm_wage_and_hours(unskilled_job_hours=20.0)
        self.assertLessEqual(wage, 2.0)
        self.assertGreater(hired, 0.0)

    def test_a_deep_unskilled_market_still_sets_the_farm_reservation(self):
        wage, hired = self._farm_wage_and_hours(unskilled_job_hours=5000.0)
        self.assertGreater(wage, 2.0)
        self.assertEqual(hired, 0.0)


if __name__ == "__main__":
    unittest.main()
