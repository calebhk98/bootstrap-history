"""`labour_state.mirror_wages`: the wage the labour core settled for each trade in each area is what everyone who reads a
wage is quoted, under the economy's market keys; a trade with no settled wage is not quoted one. Hand-built state; no game."""
QUICK_TOPIC = True

import unittest

from sim.economy import labour_state
from sim.economy.market_memory import market_key
from sim.labour.api import MarketState


def state_with_wages(wages):
    return MarketState(workers={}, trainees={}, wages=wages)


class MirrorWagesTests(unittest.TestCase):
    def test_each_settled_wage_is_quoted_under_its_trade_and_area(self):
        memory = {}
        labour_state.mirror_wages(memory, state_with_wages({"town": {"smith": 3.0, "labourer": 1.0}, "port": {"smith": 3.5}}))
        self.assertEqual(memory, {market_key("smith", "town"): 3.0, market_key("labourer", "town"): 1.0,
                                  market_key("smith", "port"): 3.5})

    def test_a_trade_with_no_settled_wage_is_not_quoted_one(self):
        memory = {}
        labour_state.mirror_wages(memory, state_with_wages({"town": {"smith": 0.0}}))
        self.assertEqual(memory, {})

    def test_a_wage_settled_again_replaces_the_one_quoted(self):
        memory = {market_key("smith", "town"): 2.0}
        labour_state.mirror_wages(memory, state_with_wages({"town": {"smith": 3.0}}))
        self.assertEqual(memory[market_key("smith", "town")], 3.0)


if __name__ == "__main__":
    unittest.main()
