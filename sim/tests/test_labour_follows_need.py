"""Non-farm hours move toward what each trade is needed for, so a wage that
signals scarcity is answered by hours and then eases back; the training
premium uses the civilisation's own interest rate."""
import random
import unittest

from sim.labour import labour_allocation
from sim.engine.data import load_civ
from sim.tests.harness import S, NODES, ORDER
from sim.labour import labour_market, wages

FARM = labour_allocation.FARM_TRADE
TOTAL_HOURS = 1000.0


def _needs(smith_hours, potter_hours):
    return {FARM: 500.0, "smith": smith_hours, "potter": potter_hours}


class HoursFollowNeedTests(unittest.TestCase):

    def test_a_short_trade_gains_hours_within_the_mobility_limit(self):
        hours = {FARM: 500.0, "smith": 50.0, "potter": 450.0}
        needs = _needs(300.0, 200.0)
        first = labour_allocation.reallocate(hours, TOTAL_HOURS, needs)
        self.assertGreater(first["smith"], hours["smith"])
        self.assertLess(first["smith"], needs["smith"])
        self.assertAlmostEqual(sum(first.values()), TOTAL_HOURS)
        ceiling = labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
        self.assertLessEqual(first["smith"] - hours["smith"], ceiling * TOTAL_HOURS)

    def test_hours_close_the_gap_over_years(self):
        hours = {FARM: 500.0, "smith": 50.0, "potter": 450.0}
        needs = _needs(300.0, 200.0)
        gaps = []
        for _year in range(200):
            hours = labour_allocation.reallocate(hours, TOTAL_HOURS, needs)
            gaps.append(needs["smith"] - hours["smith"])
        self.assertEqual(gaps, sorted(gaps, reverse=True))
        self.assertLess(gaps[-1], 0.05 * gaps[0])

    def test_wage_rises_then_eases_back_as_hours_answer(self):
        schedule = wages.WageSchedule({"smith": 5.0, "potter": 5.0}, 1.0, 1.0, 0.10)
        hours = {FARM: 500.0, "smith": 50.0, "potter": 450.0}
        needs = _needs(300.0, 200.0)
        series = []
        for _year in range(400):
            schedule.step(needs, hours)
            hours = labour_allocation.reallocate(hours, TOTAL_HOURS, needs)
            series.append(schedule.wage_per_hour("smith"))
        peak = max(series)
        self.assertGreater(peak, series[0])
        self.assertLess(series[-1], peak)
        self.assertAlmostEqual(series[-1], series[-2], places=3)

    def test_one_function_gives_the_need_to_allocation_and_wages(self):
        needed = labour_allocation.hours_needed_by_trade(
            {"smith": 0.25, "potter": 0.75}, 1000.0, 600.0)
        self.assertEqual(needed, {FARM: 600.0, "smith": 100.0, "potter": 300.0})


class TrainingPremiumUsesCivilisationRateTests(unittest.TestCase):

    def test_higher_interest_rate_gives_a_larger_premium(self):
        premiums = {}
        for rate in (0.05, 0.30):
            civ = load_civ("rome_100ad")
            civ["starting_interest_rate"] = rate
            engine = S.Sim(NODES, ORDER, random.Random(1), events=False,
                           manual=True, civ=civ)
            premiums[rate] = engine.wage_schedule().premium("smith")
        self.assertGreater(premiums[0.30], premiums[0.05])

    def test_the_default_constant_is_gone(self):
        self.assertFalse(hasattr(wages, "DEFAULT_DISCOUNT_RATE"))


if __name__ == "__main__":
    unittest.main()
