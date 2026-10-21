"""Complaint 473: a buyer's ceiling for an input is its price plus the run's margin shared by the input's cost share, and
for a tool never more than the input is worth against its cheapest substitute (the next tool in the basket, or working
by hand). A scarce input is rationed by bid inside that bound and is not bid up without one."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers, tool_fallback
from sim.economy.types import Recipe, ToolFallback

# a farm run: 10 hours of farming, wearing half a unit of iron tools; short of iron it draws one unit of wooden tools
# and takes 1.4 times the hours, short of both it works by hand at 2.5 times the hours
TOOLED = Recipe("farm", {"grain": 10.0}, {"iron": 0.5}, {"hand": 10.0}, tool_wear={"iron": 0.5},
                tool_fallbacks={"iron": (ToolFallback("wood", 1.0, 1.4, ("hand",)), ToolFallback("", 0.0, 2.5, ("hand",)))})
PRICES = {"iron": 5.0, "wood": 2.0, "grain": 10.0}
WAGES = {"hand": 1.0}
SEEDED = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})


class View:
    year = 3

    def __init__(self, prices, wages):
        self.prices, self.wages = prices, wages

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def cash(self, agent, currency):
        return 1e6

    def stock(self, agent, good, tile):
        return 0.0


def farmer(recipe_id="farm", **changes):
    base = dict(agent_id="f1", owner="lord", recipe_id=recipe_id, tile="t", capacity_runs=10.0, last_runs=5.0,
                expected_sales=5.0, expected_prices={"grain": 10.0})
    base.update(changes)
    return producers.Producer(**base)


class ValueInUseTests(unittest.TestCase):
    def test_a_tool_is_worth_what_its_cheapest_substitute_costs_the_run_per_unit(self):
        # wooden tools: one unit at 2 and 4 more hours at 1 = 6 a run, by hand 15 hours more = 15: the cheaper, over half a unit
        self.assertAlmostEqual(tool_fallback.value_in_use(TOOLED, "iron", PRICES, WAGES), 6.0 / 0.5)

    def test_a_later_tool_is_worth_its_substitute_less_its_own_extra_hours(self):
        # by hand costs 15 against wooden tools' own 4 extra hours: 11 over the unit a run draws
        self.assertAlmostEqual(tool_fallback.value_in_use(TOOLED, "wood", PRICES, WAGES), 11.0)

    def test_a_good_that_is_no_tool_or_whose_substitute_cannot_be_priced_has_no_value_in_use(self):
        self.assertIsNone(tool_fallback.value_in_use(SEEDED, "seed", PRICES, WAGES))
        self.assertIsNone(tool_fallback.value_in_use(TOOLED, "iron", {"iron": 5.0}, {}))

    def test_a_cheaper_substitute_lowers_the_value(self):
        dearer = tool_fallback.value_in_use(TOOLED, "iron", {**PRICES, "wood": 4.0}, WAGES)
        cheaper = tool_fallback.value_in_use(TOOLED, "iron", {**PRICES, "wood": 1.0}, WAGES)
        self.assertGreater(dearer, cheaper)


class InputCeilingTests(unittest.TestCase):
    def test_the_ceiling_is_the_price_plus_the_margin_share_the_input_accounts_for(self):
        self.assertAlmostEqual(producers.input_ceiling(price=2.0, margin_per_run=30.0, variable_cost_per_run=10.0), 2.0 * (1.0 + 3.0))
        self.assertEqual(producers.input_ceiling(2.0, -5.0, 10.0), 2.0)

    def test_the_ceiling_is_capped_at_the_value_in_use(self):
        self.assertEqual(producers.input_ceiling(2.0, 30.0, 10.0, value_in_use=3.0), 3.0)
        self.assertEqual(producers.input_ceiling(2.0, 30.0, 10.0, value_in_use=100.0), 8.0)

    def test_a_bid_does_not_exceed_the_margin_share_however_wide_the_margin(self):
        view = View({"grain": 100.0, "seed": 1.0}, WAGES)
        plan = producers.plan(farmer(expected_prices={"grain": 100.0}), SEEDED, view, 1e6)
        seed = [bid for bid in plan.bids if bid.good == "seed"][0]
        variable = 2.0 * 1.0 + 5.0 * 1.0       # a run's seed and hours
        self.assertLess(seed.maximum_price, 1.0 * (1.0 + 100.0 * 10.0 / variable))      # the old ceiling: the whole run margin over the seed
        self.assertAlmostEqual(seed.maximum_price, 1.0 * (1.0 + (10.0 * 100.0 - variable) / variable), delta=0.05 * seed.maximum_price)

    def test_an_iron_tool_is_not_bid_above_what_wooden_tools_save_however_scarce_and_dear(self):
        # the tool's price has run to ten times the cost of the wooden substitute; the margin would pay far more
        view = View({"iron": 50.0, "wood": 2.0, "grain": 100.0}, WAGES)
        plan = producers.plan(farmer(expected_prices={"grain": 100.0}), TOOLED, view, 1e6)
        iron = [bid for bid in plan.bids if bid.good == "iron"][0]
        self.assertLessEqual(iron.maximum_price, tool_fallback.value_in_use(TOOLED, "iron", {"iron": 50.0, "wood": 2.0}, WAGES) + 1e-9)
        self.assertLess(iron.maximum_price, iron.reference_price)       # below today's price: the run draws wooden tools

    def test_the_wooden_substitute_is_bid_for_when_it_is_the_cheaper_way(self):
        view = View({"iron": 50.0, "wood": 2.0, "grain": 100.0}, WAGES)
        plan = producers.plan(farmer(expected_prices={"grain": 100.0}), TOOLED, view, 1e6)
        wood = [bid for bid in plan.bids if bid.good == "wood"][0]
        self.assertGreaterEqual(wood.maximum_price, wood.reference_price)
        self.assertLessEqual(wood.maximum_price, 11.0 + 1e-9)


if __name__ == "__main__":
    unittest.main()
