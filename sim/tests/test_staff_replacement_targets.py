"""Complaint 640: the yearly replacement loop of the staff step as a plain function of written-out inputs."""
QUICK_TOPIC = True

import unittest

from sim.workforce.staff_replacement import replacement_targets

TARGET = 3.0
GENERIC = frozenset({"artisan", "scholar", "labourer"})


class ReplacementTargets(unittest.TestCase):
    def test_a_taught_trade_something_draws_on_is_raised_to_the_target(self):
        targets = replacement_targets({"smith": 1.0}, {"smith"}, {"smith": ["project"]}, TARGET, GENERIC)
        self.assertEqual(targets, [("smith", TARGET)])

    def test_a_taught_trade_that_lost_its_last_person_is_still_replaced(self):
        targets = replacement_targets({}, {"glassblower"}, {"glassblower": ["open concern"]}, TARGET, GENERIC)
        self.assertEqual(targets, [("glassblower", TARGET)])

    def test_a_gap_of_a_hundredth_of_a_person_or_less_is_not_chased(self):
        targets = replacement_targets({"smith": 2.99}, {"smith"}, {"smith": ["project"]}, TARGET, GENERIC)
        self.assertEqual(targets, [])

    def test_trades_nothing_draws_on_and_generic_trades_are_skipped(self):
        targets = replacement_targets({"potter": 0.0, "artisan": 0.0}, {"potter", "artisan"}, {"artisan": ["project"]}, TARGET, GENERIC)
        self.assertEqual(targets, [])

    def test_targets_come_in_sorted_trade_order(self):
        drawn_on = {"weaver": [1], "smith": [1]}
        targets = replacement_targets({"weaver": 0.0}, {"weaver", "smith"}, drawn_on, TARGET, GENERIC)
        self.assertEqual([trade for trade, _ in targets], ["smith", "weaver"])


if __name__ == "__main__":
    unittest.main()
