"""Complaints/507 stage 5: what an entry costs a producer is the calculator at the economy's prices, wages, rate and rent.
A plant that exists offers at its running cost, a new one is judged at its full cost, and the cost moves with the economy's
input prices and wages (not with the long-run table). `cost_of_making` is called with price and wage functions the test builds."""
QUICK_TOPIC = True

import unittest

from sim.prices import making_cost
from sim.tests.test_capital_charge import works_entry

RATE = 0.12
ENTRY = "widget_kg"


def cost(ore_price=1.0, wage=1.0, rate=RATE, include_plant=True, ore_known=True, wage_of=None):
    made = making_cost.cost_of_making(
        ENTRY, ENTRY, {"ore_kg": ore_price}.get if ore_known else {}.get, wage_of or {"labourer": wage}.get, rate,
        include_plant=include_plant, production={ENTRY: works_entry()})
    return None if made is None else made.unit_cost


class CostAtEconomyPricesTests(unittest.TestCase):
    def test_a_plant_that_exists_offers_at_its_running_cost_below_the_full_cost(self):
        running, full = cost(include_plant=False), cost()
        self.assertTrue(0.0 < running < full)

    def test_dearer_inputs_at_the_economy_raise_the_cost_of_making(self):
        self.assertGreater(cost(ore_price=2.0), cost())

    def test_dearer_inputs_raise_the_running_cost_too(self):
        self.assertGreater(cost(ore_price=2.0, include_plant=False), cost(include_plant=False))

    def test_dearer_wages_at_the_economy_raise_the_cost_of_making(self):
        self.assertGreater(cost(wage=2.0), cost())

    def test_a_dearer_rate_raises_the_full_cost_and_leaves_the_running_cost_alone(self):
        self.assertGreater(cost(rate=0.20), cost(rate=0.05))
        self.assertAlmostEqual(cost(rate=0.20, include_plant=False), cost(rate=0.05, include_plant=False))

    def test_an_input_with_no_price_cannot_be_costed(self):
        self.assertIsNone(cost(ore_known=False))

    def test_a_trade_with_no_wage_cannot_be_costed_rather_than_costing_nothing(self):
        self.assertIsNone(cost(wage_of={}.get))


if __name__ == "__main__":
    unittest.main()
