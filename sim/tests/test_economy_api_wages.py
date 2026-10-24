"""api.wages_by_trade_weighted weights each trade's remembered wages by last year's hours hired."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import api


def stand_in(wages, hired, idle):
    setup = types.SimpleNamespace(unskilled_trade="labourer", countries=lambda: ("home",), civ_id="home", tiles={"a": None, "b": None})
    record = types.SimpleNamespace(memory=types.SimpleNamespace(wages=wages), hours_hired=hired, hours_idle=idle)
    return types.SimpleNamespace(setup=setup, record=record)


class WeightedWageTests(unittest.TestCase):
    def test_weighted_wage_is_the_hours_hired_mean_of_the_trades_market_wages(self):
        economy = stand_in({"smith|work@a": 2.0, "smith|work@b": 4.0},
                           {"smith|work@a": 100.0, "smith|work@b": 300.0},
                           {"smith|work@a": 10.0, "smith|work@b": 0.0})
        self.assertAlmostEqual(api.wages_by_trade_weighted(economy)["smith"], 3.5)

    def test_a_trade_that_hired_no_hours_is_left_out_except_the_unskilled_trade(self):
        economy = stand_in({"smith|work@a": 2.0, "labourer|work@a": 1.0}, {"smith|work@a": 0.0},
                           {"smith|work@a": 50.0, "labourer|work@a": 5.0})
        self.assertEqual(api.wages_by_trade_weighted(economy), {"labourer": 1.0})


if __name__ == "__main__":
    unittest.main()
