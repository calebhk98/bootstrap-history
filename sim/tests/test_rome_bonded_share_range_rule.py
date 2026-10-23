"""The bonded-share range check, on numbers, so it is seen to be able to fail (Complaint 648)."""
import unittest

from sim.tests.test_rome_bonded_share_baseline_validation import bonded_share, within

QUICK_TOPIC = True


class RangeRule(unittest.TestCase):
    """The check itself, on numbers, so it is seen to be able to fail."""

    def test_a_share_outside_the_range_fails(self):
        self.assertFalse(within(0.02, 0.08, 0.15))
        self.assertFalse(within(0.30, 0.08, 0.15))
        self.assertTrue(within(0.10, 0.08, 0.15))

    def test_the_share_is_read_from_the_strata(self):
        class Stub:
            def __init__(self, members, bonded):
                self.record = type("Record", (), {"members": members})()
                self._bonded = bonded

            def is_bonded(self):
                return self._bonded
        self.assertAlmostEqual(bonded_share([Stub(90.0, False), Stub(10.0, True)])[0], 0.10)
        self.assertEqual(bonded_share([])[0], 0.0)
