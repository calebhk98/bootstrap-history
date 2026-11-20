"""Complaint 473: a buyer's ceiling for an input. Hands are hired before the year's goods change hands, so when a run buys
its inputs its wages are already committed: an input is worth its price plus its share, among the inputs, of the run's margin
and of those wages; for a tool never more than the input is worth against its cheapest substitute (the next tool in the basket,
or working by hand). A ceiling of the price plus the run's percentage margin let a small input whose price rose by more than
that margin stop a run whose hands were already paid."""

QUICK_TOPIC = True

import unittest

from sim.tests.economy_view_defaults import ViewDefaults
from sim.economy import producers, tool_fallback
from sim.economy.types import Recipe, ToolFallback

# a farm run: 10 hours of farming, wearing half a unit of iron tools; short of iron it draws one unit of wooden tools
# and takes 1.4 times the hours, short of both it works by hand at 2.5 times the hours
TOOLED = Recipe("farm", {"grain": 10.0}, {"iron": 0.5}, {"hand": 10.0}, tool_wear={"iron": 0.5},
                tool_fallbacks={"iron": (ToolFallback("wood", 1.0, 1.4, ("hand",)), ToolFallback("", 0.0, 2.5, ("hand",)))})
PRICES = {"iron": 5.0, "wood": 2.0, "grain": 10.0}
WAGES = {"hand": 1.0}
SEEDED = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})


class View(ViewDefaults):
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
    def test_the_ceiling_is_the_price_plus_the_inputs_share_of_the_margin_and_the_committed_wages(self):
        # a run whose inputs cost 10 and which has 30 of margin and committed wages to cover them: each input may cost four times its price
        self.assertAlmostEqual(producers.input_ceiling(price=2.0, room_per_run=30.0, input_cost_per_run=10.0), 2.0 * (1.0 + 3.0))
        self.assertEqual(producers.input_ceiling(2.0, -5.0, 10.0), 2.0)

    def test_the_ceiling_is_capped_at_the_value_in_use(self):
        self.assertEqual(producers.input_ceiling(2.0, 30.0, 10.0, value_in_use=3.0), 3.0)
        self.assertEqual(producers.input_ceiling(2.0, 30.0, 10.0, value_in_use=100.0), 8.0)

    def test_a_small_input_of_a_run_that_is_mostly_wages_is_bid_for_far_above_its_price(self):
        # herding: a run of 100 hours that sells for 110 and needs one unit of salt at 1: the margin is thin, the hands are hired
        herding = Recipe("herd", {"wool": 1.0}, {"salt": 1.0}, {"hand": 100.0})
        view = View({"wool": 110.0, "salt": 1.0}, WAGES)
        plan = producers.plan(farmer(expected_prices={"wool": 110.0}), herding, view, 1e6)
        salt = [bid for bid in plan.bids if bid.good == "salt"][0]
        self.assertGreater(salt.maximum_price, 50.0)       # not the price plus the run's few per cent of margin

    def test_a_bid_does_not_exceed_what_the_run_brings_in_over_its_other_costs(self):
        view = View({"grain": 100.0, "seed": 1.0}, WAGES)
        plan = producers.plan(farmer(expected_prices={"grain": 100.0}), SEEDED, view, 1e6)
        seed = [bid for bid in plan.bids if bid.good == "seed"][0]
        self.assertLessEqual(seed.maximum_price, 100.0 * 10.0 / 2.0)      # a run's grain over the seed it sows


if __name__ == "__main__":
    unittest.main()
