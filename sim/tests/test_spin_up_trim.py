"""The spin-up's workforce trim by rule set: the search rules cut each skilled trade to the hours employers plan to
want, the clearing rules leave the workforce as the years made it."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import api, rule_sets, spin_up_trim, workforce_settle


def economy_on(rule_set):
    return types.SimpleNamespace(setup=types.SimpleNamespace(rule_set=rule_set), record="record", view=lambda: "view")


class TrimByRuleSet(unittest.TestCase):
    def trims_made(self, rule_set):
        calls = []
        with mock.patch.object(workforce_settle, "trim_to_expected_hours", lambda setup, record, view: calls.append((record, view))):
            api.trim_workforce_to_expected_hours(economy_on(rule_set))
        return calls

    def test_the_search_rules_trim_the_workforce(self):
        self.assertEqual(self.trims_made("search"), [("record", "view")])

    def test_the_clearing_rules_leave_the_workforce_as_the_years_made_it(self):
        self.assertEqual(self.trims_made("clearing"), [])


class Rules(unittest.TestCase):
    def test_the_two_answers(self):
        self.assertTrue(spin_up_trim.trims())
        self.assertFalse(spin_up_trim.leaves_the_workforce())
        self.assertIs(rule_sets.RULE_SETS["search"].spin_up_trims_workforce, spin_up_trim.trims)
        self.assertIs(rule_sets.RULE_SETS["clearing"].spin_up_trims_workforce, spin_up_trim.leaves_the_workforce)


if __name__ == "__main__":
    unittest.main()
