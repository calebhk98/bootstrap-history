"""The world's unskilled fallback trade is the registry's: the flagged trade, else the fewest training years."""

QUICK_TOPIC = True

import types
import unittest

from sim.labour import trade_data


def world_with(registry):
    return types.SimpleNamespace(trades=types.SimpleNamespace(trade_registry=registry))


class FallbackTradeOfTheWorld(unittest.TestCase):

    def test_the_flagged_trade_is_the_fallback(self):
        registry = {"digger": {"family": "earth", "training_years": 0.0},
                    "porter": {"family": "carry", "training_years": 1.0, "fallback": True}}
        self.assertEqual(trade_data.fallback_trade_of(world_with(registry)), "porter")

    def test_with_none_flagged_the_trade_needing_fewest_years_is_the_fallback(self):
        registry = {"smith": {"family": "metal", "training_years": 4.0},
                    "reaper": {"family": "earth", "training_years": 0.5}}
        self.assertEqual(trade_data.fallback_trade_of(world_with(registry)), "reaper")


if __name__ == "__main__":
    unittest.main()
