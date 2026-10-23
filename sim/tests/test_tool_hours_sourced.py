"""Complaint 650: the wooden-tool hours factor is the ratio of two measured tillage rates; the rest stay labelled."""
QUICK_TOPIC = True

import json
import os
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Semyonov 1974 as reported by Shukurov et al. (arXiv 1505.05121), square metres tilled per person-hour
OAK_DIBBLE_RATE = 5.0
IRON_POINTED_DIBBLE_RATES = (6.0, 8.0)


def _farmer():
    with open(os.path.join(_ROOT, "data", "world", "trades.json"), encoding="utf-8") as handle:
        return json.load(handle)["trades"]["farmer"]


def hours_factor_from_rates(slow_rate, fast_rates):
    """Hours with the slower tool per hour with the faster one, at the midpoint of the faster tool's measured range."""
    return (sum(fast_rates) / len(fast_rates)) / slow_rate


class WoodenToolFactor(unittest.TestCase):

    def test_the_factor_is_the_ratio_of_the_measured_rates(self):
        self.assertAlmostEqual(hours_factor_from_rates(OAK_DIBBLE_RATE, IRON_POINTED_DIBBLE_RATES), 1.4)
        self.assertAlmostEqual(_farmer()["tool_hours_factor"]["wooden_tools_kg"],
                               hours_factor_from_rates(OAK_DIBBLE_RATE, IRON_POINTED_DIBBLE_RATES))

    def test_the_factor_lies_within_the_measured_range(self):
        low = IRON_POINTED_DIBBLE_RATES[0] / OAK_DIBBLE_RATE
        high = IRON_POINTED_DIBBLE_RATES[1] / OAK_DIBBLE_RATE
        self.assertTrue(low <= _farmer()["tool_hours_factor"]["wooden_tools_kg"] <= high)

    def test_the_unsourced_wooden_figures_still_name_their_retirement(self):
        with open(os.path.join(_ROOT, "data", "production", "96_wooden_tools.json"), encoding="utf-8") as handle:
            entry = json.load(handle)["materials"]["wooden_tools_kg"]
        self.assertEqual((entry["conf"], entry["retire"]), ("D", "Complaint 650"))
        self.assertIn("retire: Complaints/650", _farmer()["tool_fallback_source"])


if __name__ == "__main__":
    unittest.main()
