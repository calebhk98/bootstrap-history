"""What limits a scarce skilled trade's hours when employers bid above the training-cost ceiling
(`clearing.trained_substitute_wage`, Complaints 511, 659 and 678): the ceiling caps the expected wage, not the hours
hired, and new hands arrive as trainees through the trade's own places, not through the wage. Plain records, no game."""

QUICK_TOPIC = True

import math
import unittest
from unittest import mock

from sim.labour.market import aptitude, clearing, expectations, records, training, trades, year

REGISTRY = {
    "digger": {"family": "toil", "training_years": 0},
    "smith": {"family": "craft", "training_years": 5, "difficulty": 0.5},
}
HOURS = 2000.0
DISCOUNT = 0.05
CAREER = 30.0
DIGGERS = 20000.0
SMITHS = 500.0


def inputs(smith_maximum, smiths_wanted=SMITHS * 20.0):
    # the diggers' bid is slack (below the diggers on hand) so their wage and the digger vacancy stay put
    bids = [records.Bid("farm", "digger", "vale", DIGGERS * 0.5 * HOURS, 3.0),
            records.Bid("works", "smith", "vale", smiths_wanted * HOURS, smith_maximum)]
    return records.YearInputs(trades=trades.trade_specs(REGISTRY), bids=bids,
                              subsistence_per_worker_year={"vale": HOURS}, hours_per_worker_year=HOURS,
                              discount_rate=DISCOUNT, career_years=CAREER,
                              entrants={"vale": SMITHS}, attrition_share={"vale": 0.03})


def start():
    return records.MarketState(workers={"vale": {"digger": aptitude.split_evenly(DIGGERS),
                                                 "smith": aptitude.split_evenly(SMITHS)}})


def smith_clearing(report):
    return report.clearing("smith", "vale")


def ceiling_of(state, year_inputs):
    return clearing.trained_substitute_wage(state, year_inputs, "vale", "smith")


def years(state, year_inputs, count):
    report = None
    for _year in range(count):
        state, report = year.run_year(state, year_inputs)
    return state, report


def trainees_of(state):
    return math.fsum(math.fsum(cohort[1]) for cohort in state.trainees.get("vale", {}).get("smith", []))


class CeilingCapsTheExpectationNotTheHours(unittest.TestCase):
    """The long-run ceiling bounds what entrants expect (the clearing's heading wage), not the hours hired; this
    year's wage may pass it (Complaint 678, test_scarcity_wage_short_run.py)."""

    def test_employers_far_above_the_ceiling_are_expected_to_pay_the_ceiling(self):
        state, report = years(start(), inputs(smith_maximum=1e6), 30)
        self.assertAlmostEqual(smith_clearing(report).heading_wage, ceiling_of(state, inputs(1e6)), places=9)

    def test_every_hand_there_is_hired_while_hours_stay_wanted(self):
        _state, report = years(start(), inputs(smith_maximum=1e6), 30)
        result = smith_clearing(report)
        self.assertGreater(result.hours_wanted, result.hours_offered)
        self.assertAlmostEqual(result.hours_hired / result.hours_offered, 1.0, places=3)

    def test_a_higher_maximum_changes_neither_the_expectation_nor_the_hours(self):
        _state, high = years(start(), inputs(smith_maximum=1e6), 30)
        _state, higher = years(start(), inputs(smith_maximum=1e9), 30)
        self.assertEqual(smith_clearing(high).heading_wage, smith_clearing(higher).heading_wage)
        self.assertEqual(smith_clearing(high).hours_hired, smith_clearing(higher).hours_hired)

    def test_without_the_ceiling_the_expectation_rises_but_a_year_s_hours_hired_do_not(self):
        _state, capped = year.run_year(start(), inputs(smith_maximum=1e6))
        with mock.patch.object(clearing, "trained_substitute_wage", lambda *args, **kwargs: math.inf):
            _state, free = year.run_year(start(), inputs(smith_maximum=1e6))
        self.assertGreater(smith_clearing(free).heading_wage, smith_clearing(capped).heading_wage)
        self.assertEqual(smith_clearing(free).hours_hired, smith_clearing(capped).hours_hired)


class NewHandsComeThroughTrainingPlaces(unittest.TestCase):

    def test_a_vacancy_adds_trainees_not_smiths_in_the_year(self):
        before = start()
        after, report = year.run_year(before, inputs(smith_maximum=1e6))
        self.assertLess(aptitude.band_total(after.workers["vale"]["smith"]),
                        aptitude.band_total(before.workers["vale"]["smith"]))
        self.assertGreater(trainees_of(after), 0.0)

    def test_trainees_never_exceed_the_places_the_incumbents_teach(self):
        state = start()
        for _year in range(15):
            state, _report = year.run_year(state, inputs(smith_maximum=1e6))
            places = training.APPRENTICES_PER_MASTER * aptitude.band_total(state.workers["vale"]["smith"])
            self.assertLessEqual(trainees_of(state), places * (1.0 + 1e-9))

    def test_once_the_places_are_full_removing_the_ceiling_adds_no_trainees(self):
        capped, _report = years(start(), inputs(smith_maximum=1e6), 10)
        with mock.patch.object(clearing, "trained_substitute_wage", lambda *args, **kwargs: math.inf):
            free, _report = years(start(), inputs(smith_maximum=1e6), 10)
        full = training.APPRENTICES_PER_MASTER * aptitude.band_total(capped.workers["vale"]["smith"])
        self.assertAlmostEqual(trainees_of(capped), full, delta=0.02 * full)
        self.assertAlmostEqual(trainees_of(free), training.APPRENTICES_PER_MASTER * aptitude.band_total(free.workers["vale"]["smith"]),
                               delta=0.02 * full)

    def test_the_ceiling_alone_does_not_draw_diggers_into_the_trade(self):
        state = start()
        for _year in range(10):
            state, report = year.run_year(state, inputs(smith_maximum=1e6))
            self.assertLessEqual(report.switched.get("vale", {}).get("smith", 0.0), 1e-9)


class ExpectedIncomeIsContinuousAcrossBalance(unittest.TestCase):
    """Complaint 664: an entrant's expected income moves with how short the trade is, not to the top bid."""

    BID = 10.0

    def graduation_income(self, shortfall_share):
        # one year from a settled start; smiths wanted exceed the smiths on hand by the share given
        year_inputs = inputs(self.BID, smiths_wanted=SMITHS * (1.0 + shortfall_share))
        settled = start()      # wages already settled at the outside option, so the wage is mid-adjustment
        settled.wages = {"vale": {"digger": 1.0, "smith": 1.0}}
        _state, report = year.run_year(settled, year_inputs)
        found = expectations.income_at_graduation(start(), year_inputs, expectations.index_clearings(report.clearings),
                                                  "vale", "smith", [1.0] * aptitude.band_count())
        return found - HOURS      # over the outside option

    def test_a_sliver_of_shortage_moves_the_expectation_by_about_a_sliver(self):
        balanced = self.graduation_income(-1e-4)
        sliver = self.graduation_income(1e-4)
        half = self.graduation_income(0.5)
        self.assertGreater(half, 0.0)
        self.assertLess(abs(sliver - balanced), 0.01 * half)

    def test_the_expectation_does_not_fall_as_the_shortage_grows(self):
        shortfalls = [-1e-4, 0.0, 1e-4, 1e-2, 0.1, 0.5, 1.0]
        incomes = [self.graduation_income(share) for share in shortfalls]
        self.assertEqual(incomes, sorted(incomes))


if __name__ == "__main__":
    unittest.main()
