"""SCENARIO (Complaint 640): Complaint 473, the short part: the spin-up trace records the money stock, price level and mint's strikes, and the
money audit's edge accounts balance. These are rules of the books, so a few years of the Rome agent economy's first
stage (sim/engine/economy_port_trace.py, the command `simulator.py spin-up-trace`) hold them; a year costs about
twelve seconds. The decades-long question, whether the mint keeps the stock up with wear, is a full-length spin-up
and lives in test_spin_up_money_supply_full_length.py (Complaint 640)."""
import unittest

from sim.engine import economy_port_trace, opening_checks_run, solve_cache
from sim.engine.economy_port_key import SPIN_UP_SOURCE_MODULES, spin_up_key
from sim.engine.economy_port_setup import build_setup
from sim.tests import harness


YEARS = 40               # the full-length trace (test_spin_up_money_supply_full_length.py)
SHORT_YEARS = 4          # enough years for the books' rules
AUDIT_TOLERANCE = 0.05     # share of the years' wear that edges other than wear and the mint may account for


def cached_spin_up_trace(game, years):
    """`economy_port_trace.spin_up_trace(game, years)`, kept on disk beside the opening checks' traces."""
    setup = build_setup(game, game.state.economy.agent_economy["opening"])
    key = solve_cache.solve_key({"opening_trace": spin_up_key(setup), "years": years},
                                source_modules=SPIN_UP_SOURCE_MODULES)
    return solve_cache.cached_json(key, lambda: economy_port_trace.spin_up_trace(game, years),
                                   cache_dir=opening_checks_run.TRACE_CACHE_DIRECTORY)


class SpinUpMoneySupplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = harness.sim()
        cls.rows = cached_spin_up_trace(cls.game, SHORT_YEARS)

    def test_the_run_records_the_price_level_the_money_stock_and_the_mints_strikes_by_year(self):
        self.assertEqual(len(self.rows), SHORT_YEARS)
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

    def test_a_game_carries_how_its_spin_up_ended(self):
        result = self.game.economy.spin_up_result()
        self.assertEqual(sorted(result), ["final", "first_stage", "gap", "gaps", "measured_years", "settled", "years"])
        self.assertIsInstance(result["settled"], bool)
        self.assertGreater(result["years"], 0)


if __name__ == "__main__":
    unittest.main()
