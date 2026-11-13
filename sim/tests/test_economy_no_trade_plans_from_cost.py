"""Complaint 642: a market that traded nothing and has nothing to quote plans from what the good costs to make (taken whole, kind
cost covering); with no cost either it has no planning price, and a maker that needs the good as an input or sells it skips the run."""

QUICK_TOPIC = True

import math
import types
import unittest

import numpy as np

from sim.constants import REGISTRY
from sim.economy import goods_remember_kernel as kernel
from sim.economy import market_memory_offers, producers, unit_cost, year_remember
from sim.economy.types import QUOTE_COST_COVERING, Recipe

NAN = math.nan


def signal_of(cost, old=7.0):
    """The kernel's signal and kind for one market: no trade, no bids, no quote, the given making cost."""
    one = lambda value, kind=np.float64: np.array([value], dtype=kind)
    signal, kind, from_trade = kernel.signals(
        one(old), one(False, np.bool_), one(10.0), one(10.0), one(0, np.int64), one(0.0), one(NAN), one(0.0), one(NAN), one(0, np.int64),
        one(False, np.bool_), one(0, np.int64), one(cost), one(False, np.bool_), one(NAN), 0.5, 0.5, 0.3, 0.3, 1.0)
    return signal[0], kind[0], from_trade[0]


class KernelSignalTests(unittest.TestCase):
    def test_nothing_to_quote_plans_from_the_making_cost_whole(self):
        signal, kind, from_trade = signal_of(2.5, old=NAN)
        self.assertEqual((signal, kind, from_trade), (2.5, kernel.COST_COVERING, False))

    def test_no_cost_either_gives_no_signal_and_no_kind(self):
        signal, kind, _from_trade = signal_of(NAN)
        self.assertTrue(math.isnan(signal))
        self.assertEqual(kind, kernel.NO_QUOTE)


class PythonRuleTests(unittest.TestCase):
    def test_plan_from_cost(self):
        self.assertEqual(year_remember.plan_from_cost(2.5), (2.5, QUOTE_COST_COVERING, False))

    def test_plan_from_no_cost_or_a_zero_cost_is_no_price(self):
        self.assertEqual(year_remember.plan_from_cost(None), (None, None, False))
        self.assertEqual(year_remember.plan_from_cost(0.0), (None, None, False))

    def test_forgotten_places_are_the_untraded_markets_with_neither_quote_nor_cost(self):
        signal = np.array([NAN, NAN, 3.0, NAN])
        kind = np.array([0, 3, 0, 0])
        from_trade = np.array([False, False, False, True])
        self.assertEqual(year_remember.forgotten_places(signal, kind, from_trade), [0])


class SkipWithoutPriceTests(unittest.TestCase):
    RECIPE = Recipe("bake", {"bread": 1.0}, {"flour": 2.0}, {}, {}, {}, 10.0)

    def test_an_output_with_no_price_on_offer_is_absent_from_the_expectation(self):
        view = types.SimpleNamespace(offered_price=lambda good, area: None, area_of=lambda good, tile: "area")
        self.assertEqual(producers.expected_output_prices_at({}, "tile", self.RECIPE, view), {})

    def test_a_run_with_an_unpriced_input_costs_infinity_so_the_maker_does_not_plan_it(self):
        self.assertTrue(math.isinf(unit_cost.input_cost_per_run(self.RECIPE, {})))


class ThinTradeShareTests(unittest.TestCase):
    def test_the_blend_has_its_own_declared_temporary_heuristic_retired_by_473(self):
        declared = REGISTRY["THIN_TRADE_COST_SHARE"]
        self.assertEqual(declared["kind"], "temporary_heuristic")
        self.assertIn("473", declared["retire"])
        self.assertEqual(market_memory_offers.THIN_TRADE_COST_SHARE, declared["value"])


if __name__ == "__main__":
    unittest.main()
