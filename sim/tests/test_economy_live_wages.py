"""producers.live_wages_at: a recipe's wages read through the one wage rule (trade_wages), so a trade the memory holds no wage
for is priced, not left out and the recipe made unpriceable."""

QUICK_TOPIC = True

import math
import types
import unittest

from sim.economy import notional, producers, unit_cost
from sim.economy.market_memory import MarketMemory, YearView
from sim.economy.types import Recipe


def setup(opening_smith=None):
    opening = {"labourer": 1.0}
    if opening_smith is not None:
        opening["smith"] = opening_smith
    return types.SimpleNamespace(opening_wages=opening, unskilled_trade="labourer", currency_id="coin",
                                 trades={"labourer": types.SimpleNamespace(training_years=0.0),
                                         "smith": types.SimpleNamespace(training_years=5.0)})


def view_of(wages, the_setup):
    memory = MarketMemory(wages=wages)
    return YearView(memory, None, types.SimpleNamespace(goods=lambda: []), "coin", the_setup, lambda tile: "north")


RECIPE = Recipe("forge", {"nail": 1.0}, {}, {"smith": 2.0})


class LiveWagesAt(unittest.TestCase):
    def test_a_trade_never_cleared_anywhere_is_priced_on_its_opening_wage(self):
        wages = producers.live_wages_at("tile", RECIPE, view_of({}, setup(opening_smith=4.0)))
        self.assertEqual(wages, {"smith": 4.0})
        self.assertTrue(math.isfinite(unit_cost.labour_cost_per_run(RECIPE, wages)))

    def test_a_trade_hired_only_elsewhere_is_priced_on_this_areas_unskilled_wage_plus_its_premium(self):
        wages = producers.live_wages_at("tile", RECIPE, view_of({"smith|south": 9.0, "labourer|north": 2.0}, setup(opening_smith=4.0)))
        self.assertGreater(wages["smith"], 2.0)
        self.assertLess(wages["smith"], 9.0)
        self.assertTrue(math.isfinite(unit_cost.labour_cost_per_run(RECIPE, wages)))

    def test_a_recorded_wage_is_the_wage(self):
        self.assertEqual(producers.live_wages_at("tile", RECIPE, view_of({"smith|north": 3.5}, setup())), {"smith": 3.5})


class CostingWages(unittest.TestCase):
    def record(self, wages):
        return types.SimpleNamespace(memory=MarketMemory(wages=wages), labour=types.SimpleNamespace(
            workforce=types.SimpleNamespace(workers={}), hours_cleared_by=lambda trade, area: 0.0))

    def test_a_trade_no_area_cleared_is_costed_on_its_opening_wage(self):
        wages = notional.costing_wages(setup(opening_smith=4.0), self.record({"labourer|north": 2.0}))
        self.assertEqual(wages["labourer"], 2.0)
        self.assertEqual(wages["smith"], 4.0)

    def test_a_trade_that_cleared_keeps_its_national_wage(self):
        wages = notional.costing_wages(setup(opening_smith=4.0), self.record({"labourer|north": 2.0, "smith|south": 9.0}))
        self.assertEqual(wages["smith"], 9.0)

    def test_a_recipe_needing_a_never_cleared_trade_has_a_finite_cheapest_cost(self):
        wages = notional.costing_wages(setup(opening_smith=4.0), self.record({}))
        cost = notional.cheapest_cost(types.SimpleNamespace(recipes={"forge": RECIPE}), "nail", {}, wages, 0.0)
        self.assertEqual(cost, 8.0)


if __name__ == "__main__":
    unittest.main()
