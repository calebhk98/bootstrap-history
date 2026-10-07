"""Farm hours move toward what the farm is needed for, the rest of the hours are shared by trade, and a
wage that signals scarcity eases back once hours meet need; the training premium uses the
civilisation's own interest rate."""
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

    def test_farm_hours_move_toward_need_within_the_mobility_limit(self):
        first = labour_allocation.farm_hours_after(500.0, 900.0, TOTAL_HOURS)
        self.assertGreater(first, 500.0)
        self.assertLess(first, 900.0)
        ceiling = labour_market.OCCUPATIONAL_MOBILITY_RATE_CEILING_PER_YEAR
        self.assertLessEqual(first - 500.0, ceiling * 500.0)

    def test_farm_hours_close_the_gap_over_years_without_overshooting(self):
        farm = 500.0
        series = []
        for _year in range(200):
            farm = labour_allocation.farm_hours_after(farm, 900.0, TOTAL_HOURS)
            series.append(farm)
        self.assertEqual(series, sorted(series))
        self.assertLessEqual(series[-1], 900.0 + 1e-9)
        self.assertGreater(series[-1], 899.0)

    def test_farm_hours_leave_the_farm_when_it_is_needed_less(self):
        self.assertLess(labour_allocation.farm_hours_after(500.0, 300.0, TOTAL_HOURS), 500.0)

    def test_the_rest_of_the_hours_are_shared_by_trade_and_nothing_is_lost(self):
        hours = labour_allocation.society_hours(TOTAL_HOURS, 600.0, {"smith": 0.25, "potter": 0.75})
        self.assertEqual(hours, {FARM: 600.0, "smith": 100.0, "potter": 300.0})
        self.assertAlmostEqual(sum(hours.values()), TOTAL_HOURS)

    def test_a_wage_rises_while_a_trade_is_short_and_eases_back_once_it_is_not(self):
        schedule = wages.WageSchedule({"smith": 5.0, "potter": 5.0}, 1.0, 1.0, 0.10)
        baseline = schedule.wage_per_hour("smith")
        needs = _needs(300.0, 200.0)
        short = {FARM: 500.0, "smith": 50.0, "potter": 450.0}
        met = {FARM: 500.0, "smith": 300.0, "potter": 200.0}
        series = []
        for _year in range(20):
            schedule.step(needs, short)
            series.append(schedule.wage_per_hour("smith"))
        peak = series[-1]
        self.assertGreater(peak, baseline)
        for _year in range(400):
            schedule.step(needs, met)
        self.assertLess(schedule.wage_per_hour("smith"), peak)

    def test_one_function_gives_the_need_to_allocation_and_wages(self):
        needed = labour_allocation.hours_needed_by_trade(
            {"smith": 0.25, "potter": 0.75}, 1000.0, 600.0)
        self.assertEqual(needed, {FARM: 600.0, "smith": 100.0, "potter": 300.0})


class TrainingPremiumUsesCivilisationRateTests(unittest.TestCase):

    def test_the_schedule_prices_training_at_the_civilisations_rate(self):
        civ = load_civ("rome_100ad")
        engine = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=civ)
        schedule = engine.labour.wage_schedule()
        years = schedule.training_years["smith"]
        self.assertAlmostEqual(schedule.premium("smith"),
                               wages.training_premium(years, civ["starting_interest_rate"]))

    def test_higher_interest_rate_gives_a_larger_premium(self):
        self.assertGreater(wages.training_premium(5.0, 0.30), wages.training_premium(5.0, 0.05))

    def test_the_default_constant_is_gone(self):
        self.assertFalse(hasattr(wages, "DEFAULT_DISCOUNT_RATE"))


if __name__ == "__main__":
    unittest.main()
