"""A finished institution hands its staff over outright exactly where the yearly staff phase does not grow the pools toward a
capacity that already counts it: auto_hire off, or replace-only."""
QUICK_TOPIC = True

import unittest

from sim.workforce.staff_replacement import REPLACE_ONLY, completion_grants_staff, staff_grows


class CompletionGrant(unittest.TestCase):
    def test_off_and_replace_only_grant(self):
        self.assertTrue(completion_grants_staff(False))
        self.assertTrue(completion_grants_staff(None))
        self.assertTrue(completion_grants_staff(REPLACE_ONLY))

    def test_auto_hire_on_does_not_grant(self):
        self.assertFalse(completion_grants_staff(True))

    def test_it_is_the_opposite_of_the_staff_phase_growing(self):
        for mode in (False, True, REPLACE_ONLY):
            self.assertNotEqual(completion_grants_staff(mode), staff_grows(mode, True))


if __name__ == "__main__":
    unittest.main()
