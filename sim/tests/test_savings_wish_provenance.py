"""Complaint 606: every number behind the households' savings wish names its source or its retirement."""
import unittest

from sim import constants
from sim import constants_retirement as retirement

QUICK_TOPIC = True

SAVINGS_WISH_NUMBERS = (
    "SAVINGS_YEARS_OF_SURPLUS_INCOME",
    "SAVINGS_RATE_RESPONSE_LIMIT",
    "SAVINGS_RESPONSE_FLOOR",
    "HOUSEHOLD_TIME_PREFERENCE",
    "WEALTH_DRAWDOWN_LIMIT",
    "SPENDING_CUT_LIMIT",
)


class SavingsWishProvenanceTests(unittest.TestCase):

    def setUp(self):
        constants._import_declaring_modules()
        constants._adopt_the_canonical_registry()

    def test_each_number_has_a_source_or_a_retirement(self):
        for name in SAVINGS_WISH_NUMBERS:
            entry = constants.REGISTRY[name]
            sourced = bool((entry["source"] or "").strip())
            self.assertTrue(sourced or retirement.has_retirement(entry), name)

    def test_a_heuristic_retires_to_the_opening_fixed_point_complaint(self):
        for name in SAVINGS_WISH_NUMBERS:
            entry = constants.REGISTRY[name]
            if entry["kind"] == "temporary_heuristic":
                self.assertIn("607", entry["retire"] or "", name)


if __name__ == "__main__":
    unittest.main()
