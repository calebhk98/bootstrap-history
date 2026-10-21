"""A market with buyers and no sellers reports a cost-covering quote, so a stale low price stops drawing
households' food budget to a food nobody sells."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import market_quote
from sim.economy.economy import Economy
from sim.economy.types import QUOTE_COST_COVERING, Bid, Recipe
from sim.tests import economy_fixture as fixture

PORRIDGE, COOK = "porridge_kg", "cook_porridge"


class QuoteWithNoOffersTests(unittest.TestCase):
    def test_buyers_and_no_sellers_with_a_maker_able_to_produce_quote_the_cost(self):
        quote = market_quote.no_trade_quote([Bid("buyer", PORRIDGE, "area", "tile", 1.0, 0.0, 1.0, 0.0, 10.0)], [], cost=3.0)
        self.assertEqual((quote.kind, quote.price), (QUOTE_COST_COVERING, 3.0))

    def test_without_a_cost_or_a_finite_bid_there_is_nothing_to_quote(self):
        self.assertIsNone(market_quote.no_trade_quote([Bid("buyer", PORRIDGE, "area", "tile", 1.0, 0.0, 1.0, 0.0, 10.0)], []))


def two_food_setup():
    """The fixture with a second food, porridge, cooked from grain: a substitute in the food need."""
    recipes = fixture.recipes()
    recipes[COOK] = Recipe(COOK, {PORRIDGE: 1000.0}, {fixture.GRAIN: 1000.0}, {fixture.LABOURER: 50.0})
    specs = fixture.specs()
    specs[PORRIDGE] = dataclasses.replace(specs[fixture.GRAIN], good_id=PORRIDGE)
    basket = fixture.basket()
    needs = tuple(dataclasses.replace(need, goods=need.goods + ((PORRIDGE, 1.0),)) if need.need_id == fixture.FOOD
                  else need for need in basket.needs)
    prices = dict(fixture.small_setup().opening_prices, **{PORRIDGE: 0.4})
    return fixture.small_setup(recipes=recipes, specs=specs, basket=dataclasses.replace(basket, needs=needs),
                               opening_prices=prices)


class StaleFoodScenarioTests(unittest.TestCase):
    def setUp(self):
        fixture.households_with_a_surplus(self)

    def stale_economy(self):
        setup = two_food_setup()
        economy = Economy(setup)
        record = economy.record
        for producer_id in [key for key, producer in record.producers.items() if producer.recipe_id == COOK]:
            del record.producers[producer_id]
        stale = [key for key in record.memory.prices if key.startswith(PORRIDGE)]
        for key in stale:
            record.memory.prices[key] *= 0.001
        return setup, economy, stale

    @unittest.expectedFailure       # cause: grain's price falls to nothing in year two while the wage stays up (473 mover 1, 608), so farms cannot pay hands and the food is not made
    def test_a_food_nobody_sells_stops_starving_households(self):
        setup, economy, _stale = self.stale_economy()
        hunger = [sum(economy.step(fixture.quiet_year(setup)).hunger_by_tile.values()) for _year in range(12)]
        self.assertLess(sum(hunger[-4:]), 0.5 * sum(hunger[:4]) + 1e-9)

    def test_the_price_of_a_food_nobody_sells_is_remembered_again_and_the_book_balances(self):
        setup, economy, stale = self.stale_economy()
        for _year in range(12):
            economy.step(fixture.quiet_year(setup))
        record = economy.record
        self.assertGreater(min(record.memory.prices[key] for key in stale if key in record.memory.prices),
                           0.01 * setup.opening_prices[PORRIDGE])
        self.assertEqual(record.book.check_conservation(1e-6).breaches, ())


if __name__ == "__main__":
    unittest.main()
