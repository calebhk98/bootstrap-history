"""api.wages_by_trade_weighted weights each trade's remembered wages by last year's hours hired."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import api
from sim.economy.setup import labour_area
from sim.labour.api import MarketState
from sim.tests.labour_record_stand_in import labour_record


def stand_in(wages, hired, idle, workers=None):
    """`workers` is {(trade, tile): people}."""
    setup = types.SimpleNamespace(unskilled_trade="labourer", countries=lambda: ("home",), civ_id="home", tiles={"a": None, "b": None})
    workforce = MarketState()
    for (trade, tile), people in (workers or {}).items():
        workforce.workers.setdefault(labour_area(tile), {})[trade] = [people]
    record = types.SimpleNamespace(memory=types.SimpleNamespace(wages=wages), labour=labour_record(hired, idle, workforce=workforce))
    return types.SimpleNamespace(setup=setup, record=record)


class WeightedWageTests(unittest.TestCase):
    def test_weighted_wage_is_the_hours_hired_mean_of_the_trades_market_wages(self):
        economy = stand_in({"smith|work@a": 2.0, "smith|work@b": 4.0},
                           {"smith|work@a": 100.0, "smith|work@b": 300.0},
                           {"smith|work@a": 10.0, "smith|work@b": 0.0})
        self.assertAlmostEqual(api.wages_by_trade_weighted(economy)["smith"], 3.5)

    def test_a_trade_that_hired_no_hours_keeps_the_core_wage_weighted_by_its_people(self):
        economy = stand_in({"smith|work@a": 2.0, "smith|work@b": 4.0, "labourer|work@a": 1.0}, {},
                           {"smith|work@a": 50.0, "smith|work@b": 50.0, "labourer|work@a": 5.0},
                           workers={("smith", "a"): 30.0, ("smith", "b"): 10.0})
        self.assertAlmostEqual(api.wages_by_trade_weighted(economy)["smith"], (2.0 * 30.0 + 4.0 * 10.0) / 40.0)

    def test_a_trade_hired_nowhere_and_with_no_people_is_the_plain_mean_of_its_area_wages(self):
        economy = stand_in({"smith|work@a": 2.0, "smith|work@b": 4.0}, {}, {})
        self.assertAlmostEqual(api.wages_by_trade_weighted(economy)["smith"], 3.0)

    def test_hours_hired_in_any_area_outweigh_people_everywhere(self):
        economy = stand_in({"smith|work@a": 2.0, "smith|work@b": 4.0}, {"smith|work@a": 10.0}, {},
                           workers={("smith", "a"): 1.0, ("smith", "b"): 99.0})
        self.assertAlmostEqual(api.wages_by_trade_weighted(economy)["smith"], 2.0)

    def test_country_trade_wage_of_a_never_hired_trade_is_the_core_wage_not_the_opening_wage(self):
        economy = stand_in({"smith|work@a": 2.0, "smith|work@b": 4.0}, {}, {}, workers={("smith", "a"): 1.0, ("smith", "b"): 1.0})
        economy.setup.trades = {"smith": object(), "labourer": object()}
        economy.setup.opening_wages = {"smith": 90.0, "labourer": 1.0}
        economy.record.memory.opening_wage_level = lambda currency: 5.0
        economy.setup.currency_id = "coin"
        self.assertAlmostEqual(api.country_trade_wage(economy, "smith"), 3.0)


if __name__ == "__main__":
    unittest.main()
