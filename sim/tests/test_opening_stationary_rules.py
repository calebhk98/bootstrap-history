"""Complaints 473, 526, 545 (GitHub issue 61): the rules that make the opening a fixed point of the yearly rules, each called
on figures written out here. `opening_stationary.solve` works the stationary quantities out of a final demand (the runs that meet
it, the hours they hire, the income they pay), `opening_leisure.anchors` and `hours_hired_by_trade` split the households' time so the
hours sold equal the hours hired, and `currency.price_inflation` reads a year's inflation as a median of the goods' changes. Whether
a stepped economy then stays within the settling bounds is measured by `python3 sim/simulator.py spin-up-trace`
(Complaint 473)."""
import dataclasses
import types
import unittest

from sim.economy import currency, households_hours_offered, opening_leisure, opening_stationary
from sim.economy.setup import EconomySetup
from sim.tests import economy_fixture as fixture

QUICK_TOPIC = True

PRICES = {fixture.GRAIN: 1.0, fixture.ORE: 0.002, fixture.METAL: 5.0}
WAGES = {fixture.LABOURER: 0.5, fixture.MINER: 0.5, fixture.SMITH: 0.5}
RATE = 0.05
DEMAND = {fixture.TOWN: {fixture.GRAIN: 5000.0, fixture.METAL: 3.0}}


class StationaryQuantitiesTests(unittest.TestCase):
    def flows(self):
        return opening_stationary.solve(DEMAND, fixture.recipes(), PRICES, WAGES, RATE)

    def test_the_runs_meet_the_final_demand(self):
        flows, recipes = self.flows(), fixture.recipes()
        self.assertGreaterEqual(flows.runs[fixture.FARM] * recipes[fixture.FARM].outputs[fixture.GRAIN], 5000.0 * (1.0 - 1e-9))
        self.assertGreaterEqual(flows.runs[fixture.SMELT] * recipes[fixture.SMELT].outputs[fixture.METAL], 3.0 * (1.0 - 1e-9))

    def test_wages_plus_profit_equal_the_value_of_the_final_demand_the_opening_sized_to(self):
        flows = self.flows()
        self.assertAlmostEqual(flows.income / flows.final_value, 1.0, places=6)

    def test_hours_offered_are_counted_against_the_hours_the_runs_hire(self):
        flows = self.flows()
        demanded = flows.hours_by_trade[fixture.LABOURER]
        self.assertAlmostEqual(opening_stationary.hours_offered_over_demanded(flows.hours_by_trade, 7.0 * demanded, fixture.LABOURER), 7.0)
        self.assertIsNone(opening_stationary.hours_offered_over_demanded(flows.hours_by_trade, 100.0, "nobody_hires_this"))


class OpeningHoursTests(unittest.TestCase):
    """The opening's households split their time so the hours they sell equal the hours its runs hire (opening_leisure.py)."""

    WAGE = 2.0

    def supply(self, free_hours):
        offer = types.SimpleNamespace(trade=fixture.LABOURER, area="area", reservation_wage=self.WAGE)
        return types.SimpleNamespace(offers=[offer], faced_wage={(fixture.LABOURER, "area"): self.WAGE},
                                     parts=lambda _offer, _wage: (0.0, free_hours, free_hours))

    def test_hours_hired_are_the_runs_expected_times_each_recipes_hours(self):
        producers = {"a": types.SimpleNamespace(recipe_id=fixture.FARM, expected_sales=2.0),
                     "b": types.SimpleNamespace(recipe_id=fixture.FARM, expected_sales=3.0)}
        hired = opening_leisure.hours_hired_by_trade(producers, fixture.recipes())
        self.assertAlmostEqual(hired[fixture.LABOURER], 5.0 * fixture.recipes()[fixture.FARM].labour_hours[fixture.LABOURER])

    def test_the_anchor_leaves_workers_selling_exactly_the_hours_hired(self):
        anchors = opening_leisure.anchors(self.supply(2000.0), {fixture.LABOURER: 1500.0})
        rest = households_hours_offered.leisure_hours_kept(2000.0, self.WAGE, anchors[fixture.LABOURER])
        self.assertAlmostEqual(2000.0 - rest, 1500.0)
        self.assertGreater(anchors[fixture.LABOURER], 0.0)

    def test_the_anchor_is_stated_at_the_opening_price_level(self):
        at_one = opening_leisure.anchors(self.supply(2000.0), {fixture.LABOURER: 1500.0})
        at_two = opening_leisure.anchors(self.supply(2000.0), {fixture.LABOURER: 1500.0}, price_level=2.0)
        self.assertAlmostEqual(at_two[fixture.LABOURER], at_one[fixture.LABOURER] / 2.0)

    def test_a_trade_hired_for_all_the_hours_free_gets_no_anchor_and_keeps_no_leisure(self):
        self.assertEqual(opening_leisure.anchors(self.supply(1000.0), {fixture.LABOURER: 1000.0}), {})


class ObservedInflationTests(unittest.TestCase):
    def test_a_year_reads_inflation_as_a_median_of_the_goods_never_below_the_lowest_nor_above_the_highest(self):
        now = {"a": 1.2, "b": 0.9, "c": 1.0}
        before = {"a": 1.0, "b": 1.0, "c": 1.0}
        observed = currency.price_inflation(now, before, {"a": 1.0, "b": 1.0, "c": 1.0})
        self.assertGreaterEqual(observed, -0.1 - 1e-9)
        self.assertLessEqual(observed, 0.2 + 1e-9)
        self.assertAlmostEqual(observed, 0.0)


class SetupTests(unittest.TestCase):
    def test_no_scenario_states_the_incomes_of_its_households(self):
        self.assertNotIn("opening_income_per_head", {field.name for field in dataclasses.fields(EconomySetup)})


if __name__ == "__main__":
    unittest.main()
