"""Workers and the hidden spin-up: the search rules move them between labour areas as in any year, the clearing rules
keep them where the scenario places the people."""

QUICK_TOPIC = True

import unittest

from sim.economy import rule_sets, spin_up_migration


class RoutesOpen(unittest.TestCase):
    def test_a_year_of_play_always_has_routes(self):
        self.assertTrue(spin_up_migration.routes_open(False, True))
        self.assertTrue(spin_up_migration.routes_open(False, False))

    def test_a_hidden_year_has_routes_only_where_the_rules_move_workers(self):
        self.assertTrue(spin_up_migration.routes_open(True, True))
        self.assertFalse(spin_up_migration.routes_open(True, False))


class Rules(unittest.TestCase):
    def test_the_two_answers(self):
        self.assertTrue(spin_up_migration.workers_move())
        self.assertFalse(spin_up_migration.workers_stay())
        self.assertIs(rule_sets.RULE_SETS["search"].spin_up_moves_workers, spin_up_migration.workers_move)
        self.assertIs(rule_sets.RULE_SETS["clearing"].spin_up_moves_workers, spin_up_migration.workers_stay)


if __name__ == "__main__":
    unittest.main()
