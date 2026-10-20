"""Complaints/34: buying scholar hours bought nothing, because the project gate read the standing headcount.

The hands a household can put on a project are `hands_available` (staff, the founder, and a person per full year of
contracted hours); the gate compares them with a node's need through `research_gate.hands_short`. Both are plain
functions, called here on built numbers."""
QUICK_TOPIC = True

import unittest

from sim.agents.research_gate import hands_short
from sim.labour.hands import contracted_hours_of, hands_available

HOURS_PER_PERSON_YEAR = 2000.0


class HandsAvailableTests(unittest.TestCase):
    def test_contracted_hours_become_hands(self):
        without = hands_available(3.0, True, 0.0, HOURS_PER_PERSON_YEAR)
        with_contract = hands_available(3.0, True, 4000.0, HOURS_PER_PERSON_YEAR)
        self.assertAlmostEqual(with_contract - without, 4000.0 / HOURS_PER_PERSON_YEAR, places=9)

    def test_the_founder_is_a_pair_of_hands_while_alive(self):
        self.assertAlmostEqual(hands_available(3.0, True, 0.0, HOURS_PER_PERSON_YEAR)
                               - hands_available(3.0, False, 0.0, HOURS_PER_PERSON_YEAR), 1.0)

    def test_a_year_of_hours_is_one_person(self):
        self.assertAlmostEqual(hands_available(0.0, False, HOURS_PER_PERSON_YEAR, HOURS_PER_PERSON_YEAR), 1.0)


class ContractedHoursTests(unittest.TestCase):
    def test_only_the_trades_the_gate_counts_are_summed(self):
        hours = {"scholar": 2000.0, "carpenter": 500.0, "labourer": 70.0}
        self.assertEqual(contracted_hours_of(hours, lambda trade: trade == "scholar"), 2000.0)
        self.assertEqual(contracted_hours_of(hours, lambda trade: trade in ("carpenter", "labourer")), 570.0)
        self.assertEqual(contracted_hours_of({}, lambda trade: True), 0.0)


class GateReadsHandsTests(unittest.TestCase):
    def test_two_bought_scholar_years_clear_a_two_scholar_gap(self):
        staff, needed = 1.0, 3.0
        headcount = hands_available(staff, False, 0.0, HOURS_PER_PERSON_YEAR)
        hands = hands_available(staff, False, 2.0 * HOURS_PER_PERSON_YEAR, HOURS_PER_PERSON_YEAR)
        self.assertEqual(hands_short(needed, headcount), 2.0)
        self.assertEqual(hands_short(needed, hands), 0.0)

    def test_a_shortfall_shrinks_as_hours_are_bought(self):
        shorts = [hands_short(5.0, hands_available(1.0, True, hours, HOURS_PER_PERSON_YEAR))
                  for hours in (0.0, 2000.0, 4000.0)]
        self.assertEqual(shorts, [3.0, 2.0, 1.0])


if __name__ == "__main__":
    unittest.main()
