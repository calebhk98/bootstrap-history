"""clearing_value.clear_one_at_one_wage and wage_floor: one wage a market, last year's moved a share toward the clearing wage."""

QUICK_TOPIC = True

import unittest

from sim.labour.market import clearing_value, wage_step
from sim.labour.market.import_cost import ImportCosts
from sim.labour.market.records import EmployerHoursBid, MarketState, YearInputs
from sim.labour.market import trades

SPECS = trades.trade_specs({"digger": {"family": "earth", "training_years": 0}})
HOURS = 100.0
SUBSISTENCE = 100.0     # reservation wage of one an hour


def make_inputs(bids, ask_floor=None):
    inputs = YearInputs(trades=SPECS, bids=bids, subsistence_per_worker_year={"vale": SUBSISTENCE},
                        hours_per_worker_year=HOURS, discount_rate=0.03, career_years=30.0)
    if ask_floor is not None:
        inputs.ask_floor_per_worker_year["vale"] = ask_floor
    return inputs


def make_state(people=10.0, wage=None):
    state = MarketState(workers={"vale": {"digger": [people, 0.0, 0.0, 0.0, 0.0]}})
    if wage is not None:
        state.wages = {"vale": {"digger": wage}}
    return state


def bid(employer, hours, maximum=3.0):
    return EmployerHoursBid(employer, "digger", "vale", hours, maximum)


def clear(state, bids, inputs=None):
    inputs = make_inputs(bids) if inputs is None else inputs
    return clearing_value.clear_one_at_one_wage(state, inputs, "digger", "vale", bids, ImportCosts(state, inputs))


class ClearOneAtOneWage(unittest.TestCase):
    def test_demand_under_supply_clears_at_the_floor(self):
        # 10 people * 100 hours offered; 500 hours wanted at up to 3 an hour: wanted is 500 * (3 - 1) / (3 - 1) at the floor
        state = make_state()
        result = clear(state, [bid("a", 500.0)])
        self.assertAlmostEqual(result.wage, 1.0)
        self.assertAlmostEqual(result.hours_hired, 500.0)

    def test_a_bid_capped_at_the_floor_clears_at_the_floor(self):
        result = clear(make_state(), [bid("a", 2000.0, maximum=1.0)])
        self.assertAlmostEqual(result.wage, 1.0)
        self.assertAlmostEqual(result.hours_hired, 1000.0)      # all the hours offered, 10 * 100

    def test_no_last_wage_clears_where_offered_meets_wanted(self):
        # 2000 hours wanted over the wages 1 to 3 meet the 1000 offered where 2000 * (3 - wage) / 2 = 1000: wage 2
        state = make_state()
        result = clear(state, [bid("a", 2000.0)])
        self.assertAlmostEqual(result.wage, 2.0)
        self.assertAlmostEqual(result.hours_offered, 1000.0)
        self.assertAlmostEqual(result.hours_hired, 1000.0)

    def test_a_last_wage_moves_the_share_of_the_way_to_the_goal(self):
        state = make_state(wage=1.0)
        result = clear(state, [bid("a", 2000.0)])
        self.assertAlmostEqual(result.wage, 1.0 + wage_step.WAGE_SHARE_MOVED_PER_YEAR * (2.0 - 1.0))
        self.assertAlmostEqual(result.target_wage, 2.0)

    def test_a_market_at_its_clearing_wage_keeps_it(self):
        state = make_state()
        bids = [bid("a", 2000.0)]
        first = clear(state, bids)
        second = clear(state, bids)
        self.assertAlmostEqual(second.wage, first.wage)
        self.assertAlmostEqual(first.wage, 2.0)

    def test_hired_hours_never_exceed_offered_or_wanted(self):
        for hours in (200.0, 1000.0, 5000.0):
            result = clear(make_state(wage=1.5), [bid("a", hours), bid("b", hours, maximum=2.0)])
            self.assertLessEqual(result.hours_hired, result.hours_offered + 1e-9)
            self.assertLessEqual(result.hours_hired, result.hours_wanted + 1e-9)

    def test_the_state_is_written(self):
        state = make_state()
        result = clear(state, [bid("a", 2000.0)])
        self.assertEqual(state.wages["vale"]["digger"], result.wage)
        self.assertEqual(state.hired_hours["vale"]["digger"], result.hired_by_employer)
        self.assertAlmostEqual(state.hired_hours["vale"]["digger"]["a"], 1000.0)

    def test_an_area_with_no_outside_option_returns_none(self):
        state = MarketState(workers={"moor": {"digger": [10.0, 0.0, 0.0, 0.0, 0.0]}})
        inputs = make_inputs([])
        result = clearing_value.clear_one_at_one_wage(state, inputs, "digger", "moor", [], ImportCosts(state, inputs))
        self.assertIsNone(result)


class WageFloor(unittest.TestCase):
    def test_without_a_stated_floor_it_is_the_reservation_wage(self):
        self.assertAlmostEqual(clearing_value.wage_floor(make_inputs([]), "vale", 0.0), SUBSISTENCE / HOURS)

    def test_a_stated_floor_per_year_is_spread_over_the_hours_and_priced_for_danger(self):
        inputs = make_inputs([], ask_floor=60.0)
        inputs.value_of_life_years_of_income = 10.0
        risk = 0.05
        self.assertAlmostEqual(clearing_value.wage_floor(inputs, "vale", risk), 60.0 / HOURS * (1.0 + risk * 10.0))

    def test_an_area_with_no_outside_option_has_no_floor(self):
        self.assertIsNone(clearing_value.wage_floor(make_inputs([]), "moor", 0.0))


if __name__ == "__main__":
    unittest.main()
