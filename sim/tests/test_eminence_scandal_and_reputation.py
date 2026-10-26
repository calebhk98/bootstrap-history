"""Eminence and prominence, one rule at a time on built figures (Complaint 640): the yearly hazard and its familiarity relief, the
chance of ruin, and when and how far withdrawing from public life lowers prominence. The command, the report and the saved
withdrawal on a stand-in `self` are in test_eminence_wiring."""
QUICK_TOPIC = True

import unittest

from sim.polity import eminence_rules
from sim.polity import constants

DANGER = 30.0
FLOOR = 20.0
YEAR = 250
WAIT = constants.WITHDRAW_EVERY
MIN_FRACTION = constants.WITHDRAW_MIN_EMINENCE_FRACTION
RETENTION = constants.WITHDRAW_REPUTATION_RETENTION, constants.WITHDRAW_EMINENCE_RETENTION


def hazard(familiarity=0.0, reputation=98.0, capital=5.0e6, effect_factor=lambda value: value):
    return eminence_rules.yearly_hazard(
        reputation, capital, familiarity, constants.EMINENCE_DANGER_WEIGHT_DEFAULT, constants.EMINENCE_REPUTATION_SCALE,
        1.0e6, constants.EMINENCE_HAZARD_BASE_SCALE, constants.EMINENCE_HAZARD_REPUTATION_SHARE,
        constants.EMINENCE_HAZARD_WEALTH_SHARE, constants.EMINENCE_FAMILIARITY_RELIEF, effect_factor)


def refusal(alive=True, last=None, eminence=39.0, reputation=98.0):
    return eminence_rules.withdrawal_refusal(alive, last, YEAR, WAIT, eminence, DANGER, MIN_FRACTION, reputation, FLOOR)


class Familiarity(unittest.TestCase):
    def test_a_city_that_has_watched_you_for_a_century_is_less_alarmed_by_you(self):
        self.assertLess(hazard(familiarity=0.9), hazard(familiarity=0.0) * 0.92)

    def test_but_never_stops_being_alarmed_altogether(self):
        self.assertGreater(hazard(familiarity=0.9), hazard(familiarity=0.0) * 0.8)
        self.assertGreater(hazard(familiarity=1.0), 0.0)


class HazardShape(unittest.TestCase):
    def test_reputation_raises_it_faster_than_proportionally(self):
        low, high = hazard(reputation=40.0, capital=0.0), hazard(reputation=80.0, capital=0.0)
        self.assertAlmostEqual(high / low, 4.0)

    def test_visible_wealth_adds_to_it_up_to_the_threshold_and_no_further(self):
        self.assertLess(hazard(capital=0.0), hazard(capital=5.0e5))
        self.assertEqual(hazard(capital=1.0e6), hazard(capital=1.0e9))

    def test_what_stands_between_you_and_the_throne_shapes_it(self):
        self.assertAlmostEqual(hazard(effect_factor=lambda value: value * 2.0), 2.0 * hazard())


class ChanceOfRuin(unittest.TestCase):
    def test_nothing_below_the_danger_line_and_rising_above_it(self):
        scale = constants.EMINENCE_HAZARD_SCALE
        self.assertEqual(eminence_rules.chance_of_ruin(DANGER - 1.0, DANGER, scale), 0.0)
        self.assertAlmostEqual(eminence_rules.chance_of_ruin(DANGER + 9.0, DANGER, scale), 9.0 / scale)

    def test_the_outcomes_a_ruin_can_take_account_for_all_of_it_and_the_run_ends_in_a_part(self):
        shares = (constants.EMINENCE_OUTCOME_CONFISCATION_SHARE, constants.EMINENCE_OUTCOME_PATRON_LOST_SHARE,
                  constants.EMINENCE_OUTCOME_RUN_ENDS_SHARE)
        self.assertAlmostEqual(sum(shares), 1.0)
        self.assertLess(constants.EMINENCE_OUTCOME_RUN_ENDS_SHARE, 1.0)


class WithdrawalRefusal(unittest.TestCase):
    def test_a_prominent_founder_with_standing_to_give_up_may_withdraw(self):
        self.assertIsNone(refusal())

    def test_the_dead_cannot(self):
        self.assertEqual(refusal(alive=False), eminence_rules.WITHDRAW_DEAD)

    def test_it_cannot_be_done_twice_in_a_decade_and_can_once_enough_years_have_passed(self):
        self.assertEqual(refusal(last=YEAR - 1), eminence_rules.WITHDRAW_TOO_SOON)
        self.assertEqual(refusal(last=YEAR - WAIT + 1), eminence_rules.WITHDRAW_TOO_SOON)
        self.assertIsNone(refusal(last=YEAR - WAIT))

    def test_nobody_watching_means_nothing_to_buy_and_it_is_refused(self):
        self.assertEqual(refusal(eminence=DANGER * MIN_FRACTION - 0.1), eminence_rules.WITHDRAW_UNNOTICED)
        self.assertIsNone(refusal(eminence=DANGER * MIN_FRACTION))

    def test_a_founder_already_as_obscure_as_the_work_allows_is_refused(self):
        self.assertEqual(refusal(reputation=FLOOR + 0.25), eminence_rules.WITHDRAW_ALREADY_OBSCURE)


class AfterWithdrawal(unittest.TestCase):
    def test_prominence_falls_by_more_than_a_third_and_reputation_by_something(self):
        reputation, eminence = eminence_rules.after_withdrawal(98.0, 39.0, FLOOR, *RETENTION)
        self.assertLess(eminence, 39.0 * 0.6)
        self.assertLess(reputation, 98.0 - 5.0)

    def test_what_you_built_you_keep_reputation_never_falls_below_the_floor(self):
        for reputation in (FLOOR + 1.0, 60.0, 100.0):
            self.assertGreaterEqual(eminence_rules.after_withdrawal(reputation, 39.0, FLOOR, *RETENTION)[0], FLOOR)


if __name__ == "__main__":
    unittest.main()
