"""Complaints 554 and 473, the full-length part: baseline validations (CLAUDE.md 4.2) of the Rome agent economy's hidden
first stage run with fixed people and no shocks (the run `simulator.py spin-up-trace` prints). The subject is the
spin-up's whole length: whether the mint replaces what wears and whether the price level, wage, money and rate come
to rest are relations of the whole economy, not of one rule.

The 40-year trace is cached on disk beside the opening checks' traces and is shared with
test_spin_up_money_supply_full_length.py (same years, so one run feeds both). Cold it is about twelve seconds a year,
over the runner's default topic limit, so this file declares its own (TOPIC_SECONDS below). Later runs read the cache
until the spin-up's source modules change (Complaint 557).

`test_the_price_level_wage_money_and_rate_settle` is THE settling test for Complaint 473 and FAILS on the current
code: the spin-up does not settle (the price level and wage drift for decades). Do not loosen it; it passes when
the spin-up reaches a resting economy. The bounds are declared in sim/economy/settling.py.
"""
import unittest

from sim.economy.baseline_checks import MIN_MONEY_REPLACEMENT, money_replacement
from sim.economy.settling import SETTLING_WINDOW_YEARS, format_report, settling_report
from sim.tests import harness
from sim.tests.test_spin_up_money_supply import YEARS, cached_spin_up_trace


# A cold run builds the 40-year trace: longer than the runner's default limit (read by sim/tests/discovery.py).
TOPIC_SECONDS = 900


class RomeBaselineFullLength(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = cached_spin_up_trace(harness.sim(), YEARS)

    def test_the_mint_replaces_the_coin_that_wears(self):
        replaced = money_replacement(self.rows, SETTLING_WINDOW_YEARS)
        self.assertGreaterEqual(replaced, MIN_MONEY_REPLACEMENT)

    def test_the_price_level_wage_money_and_rate_settle(self):
        report = settling_report(self.rows)
        unsettled = [item.name for item in report if not item.settled]
        self.assertEqual(unsettled, [], "not settled over the last %d of %d years:\n%s"
                         % (SETTLING_WINDOW_YEARS, YEARS, format_report(report)))


if __name__ == "__main__":
    unittest.main()
