"""Scenarios (Complaint 640; the rules are in test_labour_population_derived): a trade's people come from its share of
work, not from a hand-written class, through the hiring cap and the national count of a whole game."""
import unittest

from .harness import *  # noqa: F401,F403


class DerivedPopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = unopened_sim(capital=1e9)
        cls.labour = cls.game.labour

    def _with_shares(self, shares):
        self.labour._non_farm_need_shares = lambda: shares
        self.addCleanup(self.labour.__dict__.pop, "_non_farm_need_shares", None)

    def test_unknown_trade_gets_supply_without_code(self):
        self._with_shares({"moddedtrade": 0.1})
        self.assertGreater(self.labour._hiring_cap_before_actors("moddedtrade"), 0.0)
        self.assertGreater(self.labour.national_trade_population("moddedtrade"), 0.0)

    def test_more_need_means_more_people(self):
        self._with_shares({"moddedtrade": 0.05})
        small_nation = self.labour.national_trade_population("moddedtrade")
        self._with_shares({"moddedtrade": 0.10})
        self.assertAlmostEqual(self.labour.national_trade_population("moddedtrade") / small_nation, 2.0)

    def test_absent_trade_stays_zero(self):
        absent = sorted(self.labour._world.trades_absent)[0]
        self.assertEqual(self.labour.national_trade_population(absent), 0.0)
        self.assertEqual(self.labour.market_supply(absent), 0.0)


if __name__ == "__main__":
    unittest.main()
