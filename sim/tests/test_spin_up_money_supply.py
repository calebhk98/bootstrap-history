"""Complaint 473: over a long spin-up the coin lost to wear is not replaced, so the money stock drains.

Runs the Rome agent economy's first stage for many years (sim/engine/economy_port_trace.py, the command
`simulator.py spin-up-trace`) on the opening a game saved, and reads the price level, the money stock and the
mint's strikes by year. Slow: one economy stepped for decades.

`test_the_money_stock_keeps_up_with_wear` FAILS on the current code and is meant to: the mint strikes next to
nothing because the silver chain stops supplying it (Complaint 473, Update). Do not loosen it; it passes when
the metal reaches the mint.
"""
import unittest

from sim.economy.metal_stock import COIN_WEAR_PER_YEAR
from sim.engine import economy_port_trace
from sim.tests import harness

YEARS = 40
DECADE = 10
AUDIT_TOLERANCE = 0.05     # share of the years' wear that edges other than wear and the mint may account for


def mean(values):
    return sum(values) / len(values)


class SpinUpMoneySupplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = harness.sim()
        cls.rows = economy_port_trace.spin_up_trace(cls.game, YEARS)

    def test_the_run_records_the_price_level_the_money_stock_and_the_mints_strikes_by_year(self):
        self.assertEqual(len(self.rows), YEARS)
        for column in economy_port_trace.COLUMNS:
            self.assertTrue(all(column in row for row in self.rows), column)
        self.assertTrue(all(row["money_supply"] > 0.0 and row["price_level"] > 0.0 for row in self.rows))
        self.assertTrue(all(row["wear"] > 0.0 for row in self.rows))

    def test_wear_is_the_steady_sink_and_the_mint_the_only_steady_source(self):
        # the money audit's edge accounts: the stock's change is what the mint struck less what wear took,
        # up to the other named edges (carriage, trade), which stay small next to wear
        wear = sum(row["wear"] for row in self.rows)
        struck = sum(row["struck"] for row in self.rows)
        change = sum(row["change"] for row in self.rows)
        self.assertLessEqual(abs(change - (struck - wear)), AUDIT_TOLERANCE * wear)

    def test_the_money_stock_keeps_up_with_wear(self):
        # Unreplaced, a stock shrinks by (1 - wear) each year, so a decade of wear is a fixed share of it. A mint
        # that replaces what wear takes keeps the stock; a lag in doing so may cost one decade's wear, and no more
        # however long the run (the same lag at every decade would be a drain).
        first = mean([row["money_supply"] for row in self.rows[:DECADE]])
        last = mean([row["money_supply"] for row in self.rows[-DECADE:]])
        one_decade_unreplaced = (1.0 - COIN_WEAR_PER_YEAR) ** DECADE
        replaced = sum(row["struck"] for row in self.rows[-DECADE:]) / sum(row["wear"] for row in self.rows[-DECADE:])
        self.assertGreaterEqual(last / first, one_decade_unreplaced,
                                "the money stock fell to %.3f of its first decade's (one decade of unreplaced wear "
                                "leaves %.3f); in the last decade the mint replaced %.2f of the wear"
                                % (last / first, one_decade_unreplaced, replaced))

    def test_a_game_carries_how_its_spin_up_ended(self):
        result = self.game.economy.spin_up_result()
        self.assertEqual(sorted(result), ["final", "first_stage", "gap", "gaps", "measured_years", "settled", "years"])
        self.assertIsInstance(result["settled"], bool)
        self.assertGreater(result["years"], 0)


if __name__ == "__main__":
    unittest.main()
