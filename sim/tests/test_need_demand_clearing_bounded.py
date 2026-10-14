"""The need-demand clearing search stops after a bounded number of demand evaluations, whatever the demand curve does."""
import math
import unittest

from sim.world import demand, need_demand

QUICK_TOPIC = True

NEED_DATA = {
    "needs": {"food": {"surplus_budget_share": 0.6, "subsistence_per_capita_per_year": 100.0},
              "adornment": {"surplus_budget_share": 0.4}},
    "goods": {"grain": {"satisfies": {"food": 1.0}}, "beads": {"satisfies": {"adornment": 1.0}}},
}
PRICES = {"grain": 2.0, "beads": 5.0}
BINS = [demand.IncomeBin(100.0, 300.0, (0.0, 1.0))]


class CountingFunction:
    """A function of price that counts how often it is asked."""

    def __init__(self, function):
        self.function = function
        self.calls = 0

    def __call__(self, price):
        self.calls += 1
        return self.function(price)


class PolishRootBounded(unittest.TestCase):
    # The polish is meant for decreasing functions; these are the ways a real curve can fail to be one.
    CURVES = {
        "constant": lambda price: 1.0,
        "not a number": lambda price: float("nan"),
        "rising": lambda price: price - 3.0,
        "noisy": lambda price: math.sin(1000.0 * math.log(price)),
        "step": lambda price: 1.0 if price < 3.0 else -1.0,
        "never positive": lambda price: -1.0,
        "never negative": lambda price: 1e-300,
    }

    def test_every_degenerate_curve_returns_within_the_step_limit_and_inside_the_bracket(self):
        for name, curve in self.CURVES.items():
            counted = CountingFunction(curve)
            root = need_demand._polish_root(counted, 1.0, 10.0)
            self.assertLessEqual(counted.calls, need_demand.POLISH_MAX_STEPS + 2, name)
            self.assertTrue(1.0 <= root <= 10.0, (name, root))


class ClearingBounded(unittest.TestCase):
    def setUp(self):
        self.model = need_demand.NeedDemandModel(NEED_DATA, {}, BINS)

    def clear(self, supply):
        calls = []
        original = self.model._influence

        def counting_influence(target):
            calls.append(target)
            return original(target)

        self.model._influence = counting_influence
        price, glut = self.model._clear("grain", supply, dict(PRICES), PRICES["grain"])
        return price, glut, calls

    def test_a_supply_above_all_demand_is_a_glut_at_the_floor_of_the_span(self):
        price, glut, _calls = self.clear(1e30)
        self.assertTrue(glut)
        self.assertLess(price, PRICES["grain"])

    def test_a_supply_below_all_demand_clears_at_the_top_of_the_span(self):
        price, glut, _calls = self.clear(0.0)
        self.assertFalse(glut)
        self.assertGreater(price, PRICES["grain"])

    def test_an_ordinary_supply_clears_at_a_positive_price_where_demand_meets_it(self):
        supply = 0.5 * self.model.final_demand(PRICES)["grain"]
        price, glut, _calls = self.clear(supply)
        self.assertFalse(glut)
        working = dict(PRICES, grain=price)
        self.assertAlmostEqual(self.model.final_demand(working)["grain"] / supply, 1.0, places=6)

    def test_clearing_with_no_population_returns_without_a_glut_search_loop(self):
        model = need_demand.NeedDemandModel(NEED_DATA, {}, [demand.IncomeBin(0.0, 300.0, (0.0, 1.0))])
        price, _glut = model._clear("grain", 10.0, dict(PRICES), PRICES["grain"])
        self.assertTrue(price > 0.0)


if __name__ == "__main__":
    unittest.main()
