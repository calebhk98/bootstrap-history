"""Complaint 523: the table of relationship checks on each civilisation's full-length opening, the one a player gets.

The checks themselves (a whole economy's price over cost, wage over floor, spin-up settled, money against wear) read an
unsettled opening (Complaint 473) and are measured by `python3 sim/simulator.py opening-checks`; this topic holds the table
of which are known to fail and for which complaint (EXPECTED_FAILURES, in full_length_opening_support.py).
"""
QUICK_TOPIC = True

import unittest

from .full_length_opening_support import CHECK_NAMES, CIVILISATIONS, EXPECTED_FAILURES


class ExpectedFailureTableTests(unittest.TestCase):
    def test_every_expected_failure_names_a_known_check_civilisation_and_complaint(self):
        for (check, civilisation), complaint in EXPECTED_FAILURES.items():
            self.assertIn(check, CHECK_NAMES)
            self.assertIn(civilisation, CIVILISATIONS)
            self.assertRegex(complaint, r"^\d+")

    def test_the_civilisations_listed_are_the_ones_shipped(self):
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        shipped = sorted(name[:-len(".json")] for name in os.listdir(os.path.join(here, "..", "..", "data", "civilizations"))
                         if name.endswith(".json") and not name.startswith("_"))
        self.assertEqual(sorted(CIVILISATIONS), shipped)


if __name__ == "__main__":
    unittest.main()
