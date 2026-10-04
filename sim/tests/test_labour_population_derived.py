"""A trade's people come from its share of work, not from a hand-written class."""
import ast
import unittest

from .harness import *  # noqa: F401,F403
from sim.labour import labour_population


class DerivedPopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = sim(capital=1e9)
        cls.labour = cls.game.labour

    def _with_shares(self, shares):
        self.labour._non_farm_need_shares = lambda: shares
        self.addCleanup(self.labour.__dict__.pop, "_non_farm_need_shares", None)

    def test_unknown_trade_gets_supply_without_code(self):
        self._with_shares({"moddedtrade": 0.1})
        self.assertGreater(self.labour._hiring_cap_before_actors("moddedtrade"), 0.0)
        self.assertGreater(self.labour.national_trade_population("moddedtrade"), 0.0)
        self.assertIsNone(self.labour._trade_density_source("moddedtrade"))

    def test_trade_with_no_demand_gets_declared_floor(self):
        self._with_shares({})
        self.assertGreater(self.labour._town_people_of_trade("moddedtrade"), 0.0)
        self.assertEqual(self.labour._trade_density_source("moddedtrade"),
                         "NO_DEMAND_TRADE_SHARE")

    def test_more_need_means_more_people(self):
        self._with_shares({"moddedtrade": 0.05})
        small_town = self.labour._town_people_of_trade("moddedtrade")
        small_nation = self.labour.national_trade_population("moddedtrade")
        self._with_shares({"moddedtrade": 0.10})
        self.assertAlmostEqual(self.labour._town_people_of_trade("moddedtrade") / small_town, 2.0)
        self.assertAlmostEqual(self.labour.national_trade_population("moddedtrade") / small_nation, 2.0)

    def test_live_society_hours_override_need(self):
        self._with_shares({"moddedtrade": 0.05})
        economy = self.game.state.economy
        self.addCleanup(setattr, economy, "society_labour_hours",
                        dict(economy.society_labour_hours))
        economy.society_labour_hours = {"moddedtrade": 30.0, "othertrade": 70.0}
        self.assertAlmostEqual(self.labour._share_of_town_work("moddedtrade"), 0.3)

    def test_absent_trade_stays_zero(self):
        absent = sorted(self.labour._world.trades_absent)[0]
        self.assertEqual(self.labour.national_trade_population(absent), 0.0)
        self.assertEqual(self.labour.market_supply(absent), 0.0)

    def test_no_trade_id_literal_in_module(self):
        with open(labour_population.__file__, encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        trade_ids = set(self.labour._world.wages)
        docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                      if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
                      and node.body and isinstance(node.body[0], ast.Expr)
                      and isinstance(node.body[0].value, ast.Constant)}
        found = [node.value for node in ast.walk(tree)
                 if isinstance(node, ast.Constant) and isinstance(node.value, str)
                 and id(node) not in docstrings and node.value in trade_ids]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
