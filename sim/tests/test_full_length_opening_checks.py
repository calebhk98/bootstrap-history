"""Complaint 523: relationship checks on each civilisation's full-length opening, the one a player gets.

The suite shortens the spin-up (`ROME_SPIN_UP_YEARS`), so a relationship that holds there says little about the
game a player opens. Each civilisation has a topic of its own (`test_full_length_opening_checks_<name>.py`, so the runner places
them side by side); each opens its civilisation on the declared-length spin-up (the shipped openings when
they match the source, else computed and kept in the disk cache), runs sim/engine/opening_checks_run.py on it and
asserts every check. Slow: a cold opening is minutes per civilisation, a warm one a cache read and a year's step.

A check that fails today is marked `expectedFailure` against the complaint that owns it (EXPECTED_FAILURES), so
the topic is green, and reports an unexpected success when that complaint's work makes it pass: remove the entry
then. A check not in the table must pass. This topic holds the table's own checks.
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

    def test_every_civilisation_has_a_topic_of_its_own(self):
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        for civilisation in CIVILISATIONS:
            self.assertTrue(os.path.exists(os.path.join(
                here, "test_full_length_opening_checks_%s.py" % civilisation.split("_")[0])), civilisation)
        shipped = sorted(name[:-len(".json")] for name in os.listdir(os.path.join(here, "..", "..", "data", "civilizations"))
                         if name.endswith(".json") and not name.startswith("_"))
        self.assertEqual(sorted(CIVILISATIONS), shipped)


if __name__ == "__main__":
    unittest.main()
