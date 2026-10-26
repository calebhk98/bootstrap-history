"""Eminence and prominence wiring on a stand-in `self` (Complaint 640): `withdraw_from_public_life` and `eminence_report`
read the household and the declared constants and hand them to the rules in eminence_rules, `settling_eminence` and
`yearly_hazard` are the figures they quote, and the household's last withdrawal is a saved field. No game."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine import eminence_rules
from sim.engine.state import HouseholdState, deserialize_state, serialize_state
from sim.engine.society_state_pressure import StatePressureMixin as Pressure
from sim.tests import event_stand_in

FLOOR = 20.0
DANGER = 30.0
YEAR = 250


class Standin(Pressure):
    """The mixin with only what the two methods read: a household, a year, a floor and no node mechanics."""
    send = event_stand_in.send
    EMINENCE_DECAY_RATE = 0.9

    def __init__(self, reputation=98.0, eminence=39.0, capital=5.0e6, last_withdrawal=None, alive=True):
        self.cfg = {"eminence_danger": DANGER}
        self.state = types.SimpleNamespace(
            household=types.SimpleNamespace(reputation=reputation, eminence=eminence, capital=capital, familiarity=0.0,
                                            last_withdrawal=last_withdrawal, log=[]),
            scenario=types.SimpleNamespace(year=YEAR))
        self.founder_alive = alive
        self.protection_updates = 0

    EMINENCE_WEALTH_VISIBLE_THRESHOLD = 1.0e9

    def standing_floor(self):
        return FLOOR

    def update_protection(self):
        self.protection_updates += 1

    def prominence_hazard(self):
        return 3.0

    def nodes_with_mechanic(self, mechanic):
        return []


class WithdrawFromPublicLifeTests(unittest.TestCase):
    def test_it_lowers_reputation_and_eminence_by_the_rule_and_leaves_the_money(self):
        standin = Standin()
        household = standin.state.household
        accepted, _message = standin.withdraw_from_public_life()
        self.assertTrue(accepted)
        expected = eminence_rules.after_withdrawal(98.0, 39.0, FLOOR, Pressure.WITHDRAW_REPUTATION_RETENTION,
                                                   Pressure.WITHDRAW_EMINENCE_RETENTION)
        self.assertEqual((household.reputation, household.eminence), expected)
        self.assertEqual(household.capital, 5.0e6)

    def test_it_records_the_year_and_the_log_line_and_refreshes_protection(self):
        standin = Standin()
        standin.withdraw_from_public_life()
        household = standin.state.household
        self.assertEqual(household.last_withdrawal, YEAR)
        self.assertEqual([(year, line.kind) for year, line in household.log], [(YEAR, "withdrew_from_public_life")])
        self.assertEqual(standin.protection_updates, 1)

    def test_a_refusal_changes_nothing(self):
        standin = Standin(last_withdrawal=YEAR - 1)
        accepted, _message = standin.withdraw_from_public_life()
        self.assertFalse(accepted)
        self.assertEqual((standin.state.household.reputation, standin.state.household.eminence), (98.0, 39.0))
        self.assertEqual(standin.state.household.log, [])


class EminenceReportTests(unittest.TestCase):
    def setUp(self):
        self.report = Standin().eminence_report()

    def test_it_settles_where_the_rule_says(self):
        self.assertEqual(self.report["settles_at_if_nothing_changes"],
                         round(eminence_rules.settling_eminence(3.0, Standin.EMINENCE_DECAY_RATE), 1))

    def test_the_chance_of_ruin_is_the_rules_chance_at_the_present_eminence(self):
        self.assertEqual(self.report["chance_of_ruin_this_year"],
                         round(eminence_rules.chance_of_ruin(39.0, DANGER, Pressure.EMINENCE_HAZARD_SCALE), 4))

    def test_the_run_ends_in_only_a_part_of_the_events_that_land(self):
        self.assertAlmostEqual(self.report["chance_the_run_ENDS_this_year"],
                               self.report["chance_of_ruin_this_year"] * Pressure.EMINENCE_OUTCOME_RUN_ENDS_SHARE, places=4)
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


class LastWithdrawalIsSavedTests(unittest.TestCase):
    def test_it_is_written_to_the_save(self):
        blob = serialize_state(HouseholdState(capital=1.0, last_withdrawal=YEAR))
        self.assertEqual(blob["last_withdrawal"], YEAR)

    def test_it_is_read_back_from_the_save(self):
        blob = serialize_state(HouseholdState(capital=1.0))
        blob["last_withdrawal"] = YEAR
        self.assertEqual(deserialize_state(blob, HouseholdState).last_withdrawal, YEAR)


if __name__ == "__main__":
    unittest.main()
