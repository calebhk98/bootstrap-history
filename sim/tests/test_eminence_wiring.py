"""Eminence and prominence wiring (Complaint 640): `withdraw_from_public_life` and `eminence_report` read the seat and the declared
constants and hand them to the rules in eminence_rules; `settling_eminence` and `yearly_hazard` are the figures they quote. The
polity module on plain values, no game."""
QUICK_TOPIC = True

import unittest

from sim.polity import constants, eminence_rules
from sim.polity.state import PolitySeat
from sim.reporting.api import RecordEvent
from sim.tests import module_harness, polity_host

FLOOR = 20.0
DANGER = 30.0
YEAR = 250


def host(reputation=98.0, eminence=39.0, capital=5.0e6, last_withdrawal=None, alive=True):
    """The module with a household at the given standing, a floor and a danger line, and no protection-giving works."""
    seat = PolitySeat(reputation=reputation, eminence=eminence, last_withdrawal=last_withdrawal)
    return polity_host.build(seat=seat, year=YEAR, danger_lines={"eminence": DANGER, "suspicion": 100.0}, standing_floor=FLOOR,
                             acting_balance=capital, founder={"alive": alive, "policy": {}}, revenue_estimate=1.0)


class WithdrawFromPublicLifeTests(unittest.TestCase):
    def test_it_lowers_reputation_and_eminence_by_the_rule_and_leaves_the_money(self):
        module = host()
        accepted, _message = module.withdraw_from_public_life()
        self.assertTrue(accepted)
        expected = eminence_rules.after_withdrawal(98.0, 39.0, FLOOR, constants.WITHDRAW_REPUTATION_RETENTION,
                                                   constants.WITHDRAW_EMINENCE_RETENTION)
        self.assertEqual((module.seat.reputation, module.seat.eminence), expected)

    def test_it_records_the_year_and_the_log_line_and_refreshes_protection(self):
        module = host()
        module.withdraw_from_public_life()
        self.assertEqual(module.seat.last_withdrawal, YEAR)
        self.assertEqual([(command.kind) for command in module_harness.sent(module) if isinstance(command, RecordEvent)],
                         ["withdrew_from_public_life"])
        self.assertGreater(module.seat.protection, 0.0)   # protection was worked out again from the lowered reputation

    def test_a_refusal_changes_nothing(self):
        module = host(last_withdrawal=YEAR - 1)
        accepted, _message = module.withdraw_from_public_life()
        self.assertFalse(accepted)
        self.assertEqual((module.seat.reputation, module.seat.eminence), (98.0, 39.0))
        self.assertEqual(module_harness.sent(module), [])


class EminenceReportTests(unittest.TestCase):
    def setUp(self):
        module = host()
        module.prominence_hazard = lambda: 3.0
        self.report = module.eminence_report()

    def test_it_settles_where_the_rule_says(self):
        self.assertEqual(self.report["settles_at_if_nothing_changes"],
                         round(eminence_rules.settling_eminence(3.0, constants.EMINENCE_DECAY_RATE), 1))

    def test_the_chance_of_ruin_is_the_rules_chance_at_the_present_eminence(self):
        self.assertEqual(self.report["chance_of_ruin_this_year"],
                         round(eminence_rules.chance_of_ruin(39.0, DANGER, constants.EMINENCE_HAZARD_SCALE), 4))

    def test_the_run_ends_in_only_a_part_of_the_events_that_land(self):
        self.assertAlmostEqual(self.report["chance_the_run_ENDS_this_year"],
                               self.report["chance_of_ruin_this_year"] * constants.EMINENCE_OUTCOME_RUN_ENDS_SHARE, places=4)
        self.assertLess(self.report["chance_the_run_ENDS_this_year"], self.report["chance_of_ruin_this_year"])

    def test_the_outcomes_it_lists_account_for_every_event(self):
        self.assertAlmostEqual(sum(self.report["if_it_lands_it_is"].values()), 1.0)


class SettlingEminenceTests(unittest.TestCase):
    def test_eminence_settles_where_a_year_of_decay_cancels_a_year_of_gain(self):
        decay, gain = 0.9, 3.0
        settled = eminence_rules.settling_eminence(gain, decay)
        self.assertAlmostEqual(settled * decay + gain, settled)

    def test_a_larger_gain_settles_higher(self):
        self.assertGreater(eminence_rules.settling_eminence(4.0, 0.9), eminence_rules.settling_eminence(3.0, 0.9))


class WealthTermTests(unittest.TestCase):
    def hazard_share(self, money_per_hour):
        """The hazard at one capital in labour hours, as a share of the hazard at saturated wealth, in a coin worth `money_per_hour`."""
        threshold_hours, capital_hours = 5.0e6, 1.0e6
        def hazard(capital):
            return eminence_rules.yearly_hazard(0.0, capital, 0.0, 0.5, 100.0, threshold_hours * money_per_hour, 2.2,
                                                0.7, 0.3, 0.15, lambda value: value)
        return hazard(capital_hours * money_per_hour) / hazard(threshold_hours * money_per_hour)

    def test_the_same_capital_in_labour_hours_is_the_same_wealth_term_in_any_coin(self):
        self.assertAlmostEqual(self.hazard_share(0.5), self.hazard_share(0.5 / 1000.0), places=12)
        self.assertGreater(self.hazard_share(0.5), 0.0)


if __name__ == "__main__":
    unittest.main()
