"""Complaint 473, the full-length part: over a long spin-up the coin lost to wear must be replaced, or the money stock
drains. A baseline validation (CLAUDE.md 4.2) whose subject is a spin-up of decades: no single rule holds it, since
whether the mint strikes depends on the metal chain, the price level and the mint's hours together.

Reads the 40-year trace of the Rome agent economy's first stage (the command `simulator.py spin-up-trace`) through the
disk cache beside the opening checks' traces. Cold, that is one economy stepped for forty years (about twelve seconds a
year), over the runner's topic limit: run it with `python3 -m sim.tests --slow --only spin_up_money_supply_full_length
--topic-seconds 900` once, and later runs read the cache until the spin-up's source modules change (Complaint 557).

`test_the_money_stock_keeps_up_with_wear` FAILS on the current code and is meant to (Complaint 473, open): the mint
strikes next to nothing because the silver chain stops supplying it. Do not loosen it; it passes when the metal
reaches the mint. The short part of this topic is test_spin_up_money_supply.py.
"""
import unittest

from sim.economy.metal_stock import COIN_WEAR_PER_YEAR
from sim.tests import harness
from sim.tests.test_spin_up_money_supply import YEARS, cached_spin_up_trace

DECADE = 10


def mean(values):
    return sum(values) / len(values)


class SpinUpMoneySupplyFullLength(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = cached_spin_up_trace(harness.sim(), YEARS)

    def test_the_money_stock_keeps_up_with_wear(self):
        # Unreplaced, a stock shrinks by (1 - wear) each year, so a decade of wear is a fixed share of it. A mint
        # that replaces what wear takes keeps the stock; a lag in doing so may cost one decade's wear, and no more
        # however long the run (the same lag at every decade would be a drain).
        first = mean([row["money_supply"] for row in self.rows[:DECADE]])
        last = mean([row["money_supply"] for row in self.rows[-DECADE:]])
        one_decade_unreplaced = (1.0 - COIN_WEAR_PER_YEAR) ** DECADE
        replaced = sum(row["struck"] for row in self.rows[-DECADE:]) / sum(row["wear"] for row in self.rows[-DECADE:])
        self.assertGreaterEqual(last / first, one_decade_unreplaced,
                                "Complaint 473 (open): the money stock fell to %.3f of its first decade's (one decade of unreplaced wear "
                                "leaves %.3f); in the last decade the mint replaced %.2f of the wear"
                                % (last / first, one_decade_unreplaced, replaced))


if __name__ == "__main__":
    unittest.main()
