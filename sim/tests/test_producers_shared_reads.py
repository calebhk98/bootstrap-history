"""`producers.next_expectations` reads the inputs' prices from the live prices its caller passes, and
`shortfall_at_working_scale` / `share_that_pays` take the expected output prices their caller has: over random
recipes, producers and markets each equals the call that reads them itself."""

QUICK_TOPIC = True

import random
import unittest

import math

from sim.economy import producers, producers_close, unit_cost
from sim.economy.types import Recipe

GOODS = ["grain", "seed", "iron", "tool", "cloth", "wool"]
TRADES = ["hand", "smith"]


class View:
    year = 3

    def __init__(self, generator, with_clearing):
        self.prices = {good: generator.uniform(0.2, 9.0) for good in GOODS if generator.random() < 0.85}
        self.cleared = {good: generator.uniform(0.2, 12.0) for good in GOODS if generator.random() < 0.5}
        self.wages = {trade: generator.uniform(0.1, 3.0) for trade in TRADES if generator.random() < 0.9}
        self.held = {good: generator.choice([0.0, generator.uniform(0.0, 40.0)]) for good in GOODS}
        if with_clearing:
            self.cleared_price = lambda good, area: self.cleared.get(good)

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

    def basket_price_level(self, currency):
        return 1.0

    def expected_inflation(self, currency):
        return 0.0

    def cash(self, agent, currency):
        return 0.0

    def stock(self, agent, good, tile):
        return self.held.get(good, 0.0)


def recipe_of(generator):
    names = generator.sample(GOODS, 5)
    outputs = {good: generator.uniform(1.0, 20.0) for good in names[:generator.randint(1, 2)]}
    inputs = {good: generator.uniform(0.5, 5.0) for good in names[2:2 + generator.randint(0, 2)]}
    plant = {names[4]: generator.uniform(1.0, 6.0)} if generator.random() < 0.5 and names[4] not in outputs else {}
    hours = {trade: generator.uniform(1.0, 8.0) for trade in TRADES[:generator.randint(1, 2)]}
    return Recipe("r", outputs, inputs, hours, plant_goods=plant, plant_life_years=10.0 if plant else 0.0)


def producer_of(generator, recipe):
    expected = {good: generator.uniform(0.3, 10.0) for good in [*recipe.outputs, *recipe.inputs] if generator.random() < 0.6}
    return producers.Producer("p", "owner", "r", "tile", generator.uniform(0.0, 30.0), generator.uniform(0.5, 1.2), expected,
                              cash_target=generator.uniform(0.0, 100.0), expected_sales=generator.choice([0.0, 5.0, 25.0]),
                              last_runs=generator.choice([-1.0, 0.0, 7.0]), land_rent_per_run=generator.choice([0.0, 0.7]))


class SharedReadsTests(unittest.TestCase):
    def test_equal_to_the_calls_that_read_for_themselves(self):
        generator = random.Random(5)
        for _case in range(500):
            recipe = recipe_of(generator)
            producer = producer_of(generator, recipe)
            view = View(generator, generator.random() < 0.7)
            live = producers.live_input_prices(producer, recipe, view)
            wages = producers.live_wages(producer, recipe, view)
            self.assertEqual(producers.next_expectations(producer, recipe, view),
                             producers.next_expectations(producer, recipe, view, live, wages))
            outputs = producers.expected_output_prices(producer, recipe, view)
            shortfall = generator.uniform(0.0, 80.0)
            self.assertEqual(producers.share_that_pays(producer, recipe, view),
                             producers.share_that_pays(producer, recipe, view, outputs))
            self.assertEqual(producers.shortfall_at_working_scale(producer, recipe, view, shortfall),
                             producers.shortfall_at_working_scale(producer, recipe, view, shortfall, outputs))

    def test_expected_run_reads_a_price_only_where_there_is_no_expectation(self):
        generator = random.Random(6)
        for _case in range(500):
            recipe = recipe_of(generator)
            producer = producer_of(generator, recipe)
            view = View(generator, True)
            expectations = {good: generator.uniform(0.3, 9.0) for good in recipe.outputs if generator.random() < 0.5}
            inputs = producers.live_input_prices(producer, recipe, view)
            wages = producers.live_wages(producer, recipe, view)
            self.assertEqual(old_expected_run(producer, recipe, view, expectations, inputs, wages),
                             producers_close._expected_run(producer, recipe, view, expectations, inputs, wages))


def old_expected_run(producer, recipe, view, expectations, inputs, wages):
    prices = {good: expectations.get(good, view.price(good, view.area_of(good, producer.tile)))
              for good in recipe.outputs}
    if any(price is None for price in prices.values()):
        return 0.0, math.inf
    prices = producers_close._behind_the_stock(producer, recipe, view, prices, ())
    cost = unit_cost.variable_cost_per_run(recipe, inputs, wages, producer.land_rent_per_run)
    if not math.isfinite(cost):
        return 0.0, math.inf
    return unit_cost.revenue_per_run(recipe, prices) * producer.yield_factor, cost


if __name__ == "__main__":
    unittest.main()
