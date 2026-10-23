"""Complaint 473, Update 14: the loop that makes the small economy's staple and labourer wage alternate year to year.

A producer's plan follows its expected price, and the expectation moves only part of the way to each year's price, so a
price that alternates is met by a plan that alternates less. The hours households sell follow the leisure anchor,
which is scaled by the price level; the level they scale it by is the level they perceive, moved part of the way to
last year's chained level (`MarketMemory.perceived_price_levels`), so a level that alternates does not swing the anchor
at full amplitude."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers, year_labour
from sim.economy.economy import Economy
from sim.economy.market_memory import MarketMemory
from sim.economy.replaced import replaced
from sim.economy.types import Recipe
from sim.tests import economy_fixture as fixture

RECIPE = Recipe("make", {"grain": 10.0}, {}, {"hand": 5.0})
MIDDLE_PRICE = 0.5          # a run's labour costs 5 at the wage below, its output sells for 5 at this price
WAGE = 1.0


class PricesView:
    year = 3

    def __init__(self, price):
        self.latest = price

    def price(self, good, area):
        return self.latest

    def wage(self, trade, area):
        return WAGE

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
        return 1.0e9

    def stock(self, agent, good, tile):
        return 0.0


def producer_at(price):
    return producers.Producer("p", "owner", "make", "tile", 100.0, 1.0, {"grain": price}, cash_target=0.0,
                              expected_sales=55.0, last_runs=55.0)


def one_year(producer, price):
    """The producer after a year in which the market showed `price`: (runs it planned at the start, producer at the end)."""
    view = PricesView(price)
    runs = producers.plan(producer, RECIPE, view, 1.0e9).runs
    expectations = producers.next_expectations(producer, RECIPE, view)
    return runs, replaced(producer, expected_prices=expectations, last_runs=runs, expected_sales=runs)


class ProducerFollowsALaggedExpectation(unittest.TestCase):
    def swing_of(self, prices):
        producer = producer_at(MIDDLE_PRICE)
        runs = []
        for price in prices:
            planned, producer = one_year(producer, price)
            runs.append(planned)
        return max(runs[-8:]) - min(runs[-8:])

    def test_an_alternating_price_does_not_alternate_output_at_full_amplitude(self):
        alternating = [MIDDLE_PRICE * (1.0 + 0.05 * (-1) ** year) for year in range(40)]
        full_response = producers.plan(producer_at(MIDDLE_PRICE * 1.05), RECIPE, PricesView(MIDDLE_PRICE * 1.05), 1.0e9).runs \
            - producers.plan(producer_at(MIDDLE_PRICE * 0.95), RECIPE, PricesView(MIDDLE_PRICE * 0.95), 1.0e9).runs
        self.assertGreater(full_response, 0.0)
        self.assertLess(self.swing_of(alternating), 0.5 * full_response)

    def test_a_step_in_the_price_is_followed_without_overshoot(self):
        stepped = MIDDLE_PRICE * 1.1
        producer = producer_at(MIDDLE_PRICE)
        runs = []
        for _year in range(60):
            planned, producer = one_year(producer, stepped)
            runs.append(planned)
        settled = runs[-1]
        self.assertGreater(settled, runs[0])
        self.assertTrue(all(after >= before - 1e-9 for before, after in zip(runs, runs[1:])), runs)
        self.assertLessEqual(max(runs), settled + 1e-9)


class HouseholdsPerceiveTheLevelWithALag(unittest.TestCase):
    def test_an_alternating_chained_level_reaches_the_perceived_level_damped(self):
        memory = MarketMemory()
        chained, perceived = [], []
        for year in range(30):
            memory.note_basket_price_level("coin", 1.0, observed_inflation=0.05 * (-1) ** year)
            chained.append(memory.price_levels["coin"])
            perceived.append(memory.perceived_price_levels["coin"])
        self.assertGreater(abs(chained[-1] / chained[-2] - 1.0), 0.04)
        self.assertLess(abs(perceived[-1] / perceived[-2] - 1.0), 0.5 * abs(chained[-1] / chained[-2] - 1.0))

    def test_a_steady_level_is_perceived_as_it_is_in_time(self):
        memory = MarketMemory()
        for _year in range(60):
            memory.note_basket_price_level("coin", 1.0, observed_inflation=0.02)
        self.assertAlmostEqual(memory.perceived_price_levels["coin"] / memory.price_levels["coin"], 1.0, delta=0.05)

    def test_the_leisure_anchor_is_scaled_by_the_perceived_level(self):
        setup = fixture.stationary_setup()
        economy = Economy(setup)
        economy.step(fixture.quiet_year(setup))
        economy.record.leisure_anchor_wage = {fixture.LABOURER: 1.0}
        economy.record.memory.price_levels[setup.currency_id] = 2.0
        economy.record.memory.perceived_price_levels[setup.currency_id] = 1.5
        view = economy.view()
        outside = year_labour.outside_option_by_tile(setup, economy.record, view)
        offers = year_labour.labour_offers(setup, economy.record, view, outside)
        supply = economy._hour_supply(offers, view, outside)
        self.assertAlmostEqual(supply.anchor_wage[fixture.LABOURER], 1.5)


if __name__ == "__main__":
    unittest.main()
