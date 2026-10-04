"""Labour-core clearing over plain records: wages, premiums, recruitment friction, poaching."""
import copy
import unittest

from sim.labour.market import aptitude, clearing, trades
from sim.labour.market.records import Bid, MarketState, YearInputs

SPECS = trades.trade_specs({"digger": {"family": "earth", "training_years": 0},
                            "healer": {"family": "care", "training_years": 5}})
HOURS = 100.0
SUBSISTENCE = 100.0   # reservation wage of one per hour


def make_inputs(bids):
    return YearInputs(trades=SPECS, bids=bids, subsistence_per_worker_year={"vale": SUBSISTENCE},
                      hours_per_worker_year=HOURS, discount_rate=0.03, career_years=30.0)


def make_state(people=10.0, wage=None):
    state = MarketState(workers={"vale": {"digger": [people, 0.0, 0.0, 0.0, 0.0]}})
    if wage is not None:
        state.wages = {"vale": {"digger": wage}}
    return state


def bid(employer, hours, maximum=3.0, premium=0.0, trade="digger"):
    return Bid(employer, trade, "vale", hours, maximum, premium)


def run(state, bids):
    return clearing.clear_all(state, make_inputs(bids))[0]


class WageMovement(unittest.TestCase):
    def test_excess_demand_raises_wage_toward_target(self):
        state = make_state(wage=1.0)
        target = clearing.clearing_target(1.0, 1000.0, [bid("a", 2000.0)])
        wages = [run(state, [bid("a", 2000.0)]).wage for _ in range(4)]
        self.assertTrue(wages[0] < wages[1] < wages[2] < wages[3] <= target)
        self.assertGreater(wages[0], 1.0)

    def test_glut_holds_wage_near_reservation(self):
        state = make_state(people=100.0, wage=1.0)
        result = run(state, [bid("a", 500.0)])
        self.assertAlmostEqual(result.wage, 1.0)

    def test_no_bids_keeps_wage_and_hires_nothing(self):
        state = make_state(wage=2.5)
        result = run(state, [])
        self.assertEqual(result.hours_hired, 0.0)
        self.assertEqual(result.wage, 2.5)
        self.assertEqual(state.wages["vale"]["digger"], 2.5)


class PremiumAndFriction(unittest.TestCase):
    def test_premium_payer_fills_first_and_pays_more(self):
        result = run(make_state(wage=1.0), [bid("plain", 800.0), bid("rich", 800.0, premium=0.5)])
        self.assertGreater(result.hired_by_employer["rich"], result.hired_by_employer["plain"])
        self.assertGreater(result.paid_by_employer["rich"], result.paid_by_employer["plain"])

    def test_large_new_bid_fills_over_years(self):
        state = make_state(people=10.0, wage=1.0)
        bids = [bid("big", 1000.0)]
        first = run(state, bids).hired_by_employer["big"]
        second = run(state, bids).hired_by_employer["big"]
        self.assertLess(first, 1000.0)
        self.assertGreater(second, first)

    def test_premium_raises_fill_fraction(self):
        plain = run(make_state(people=40.0, wage=1.0), [bid("a", 3000.0)]).hired_by_employer["a"]
        paying = run(make_state(people=40.0, wage=1.0), [bid("a", 3000.0, premium=0.5)]).hired_by_employer["a"]
        self.assertGreater(paying, plain)


class Poaching(unittest.TestCase):
    def test_hours_move_from_low_payer_to_high_payer(self):
        state = make_state(people=10.0, wage=1.0)
        state.hired_hours = {"vale": {"digger": {"low": 1000.0}}}
        result = run(state, [bid("low", 1000.0), bid("high", 500.0, premium=0.5)])
        self.assertGreater(result.hired_by_employer.get("high", 0.0), 0.0)
        self.assertLess(result.hired_by_employer["low"], 1000.0)


class Conservation(unittest.TestCase):
    def test_never_hires_more_than_offered_or_wanted(self):
        state = make_state(people=5.0, wage=1.0)
        state.hired_hours = {"vale": {"digger": {"a": 300.0, "b": 400.0}}}
        bids = [bid("a", 600.0), bid("b", 600.0, premium=0.2), bid("c", 600.0, premium=0.4)]
        for _ in range(3):
            result = run(state, bids)
            self.assertLessEqual(result.hours_hired, result.hours_offered + 1e-9)
            self.assertLessEqual(result.hours_hired, result.hours_wanted + 1e-9)
            for hours in result.hired_by_employer.values():
                self.assertLessEqual(hours, 600.0 + 1e-9)

    def test_deterministic(self):
        bids = [bid("a", 700.0), bid("b", 700.0, premium=0.3), bid("c", 700.0)]
        first_state, second_state = make_state(wage=1.0), copy.deepcopy(make_state(wage=1.0))
        self.assertEqual(run(first_state, bids), run(second_state, bids))

    def test_other_trade_with_made_up_id_clears_separately(self):
        state = MarketState(workers={"vale": {"healer": [4.0, 0.0, 0.0, 0.0, 0.0]}})
        found = clearing.clear_all(state, make_inputs([bid("a", 100.0, trade="healer")]))
        self.assertEqual([(each.trade, each.area) for each in found], [("healer", "vale")])



class ManyTranchesTests(unittest.TestCase):
    def test_many_employers_at_falling_wages_clear_without_error(self):
        specs = trades.trade_specs({"digger": {"family": "toil", "training_years": 0},
                                    "carver": {"family": "craft", "training_years": 3}})
        state = MarketState(workers={"vale": {"carver": aptitude.split_evenly(31.0)}})
        bids = [Bid("employer%d" % index, "carver", "vale", 6.0 * 2000.0 / 1.0, 3.0 * (1.3 - 0.15 * index))
                for index in range(5)]
        year_inputs = YearInputs(trades=specs, bids=bids, subsistence_per_worker_year={"vale": 1600.0},
                                         hours_per_worker_year=2000.0, discount_rate=0.05, career_years=30.0)
        for _year in range(5):
            for result in clearing.clear_all(state, year_inputs):
                self.assertIsInstance(result.hours_hired, float)
                self.assertLessEqual(result.hours_hired, result.hours_offered + 1e-6)


if __name__ == "__main__":
    unittest.main()
