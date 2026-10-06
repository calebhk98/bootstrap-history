"""A market with buyers and no sellers: its remembered price moves toward what the good costs to make,
so a stale low price stops drawing households' food budget to a food nobody sells."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import market_memory_offers
from sim.economy.economy import Economy
from sim.economy.types import Recipe
from sim.tests import economy_fixture as fixture

PORRIDGE, COOK = "porridge_kg", "cook_porridge"


class PriceAfterNoOffersTests(unittest.TestCase):
    def test_partway_to_the_cost_both_ways(self):
        share = market_memory_offers.NO_OFFER_MEMORY_SHARE
        self.assertAlmostEqual(market_memory_offers.price_after_no_offers(1.0, 3.0), 1.0 + share * 2.0)
        self.assertAlmostEqual(market_memory_offers.price_after_no_offers(3.0, 1.0), 3.0 - share * 2.0)

    def test_nothing_to_move_from_or_to(self):
        self.assertIsNone(market_memory_offers.price_after_no_offers(None, 1.0))
        self.assertIsNone(market_memory_offers.price_after_no_offers(1.0, None))


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
    def test_a_food_nobody_sells_stops_starving_households(self):
        setup = two_food_setup()
        economy = Economy(setup)
        record = economy.record
        for producer_id in [key for key, producer in record.producers.items() if producer.recipe_id == COOK]:
            del record.producers[producer_id]
        stale = [key for key in record.memory.prices if key.startswith(PORRIDGE)]
        for key in stale:
            record.memory.prices[key] *= 0.001
        hunger = [sum(economy.step(fixture.quiet_year(setup)).hunger_by_tile.values()) for _year in range(12)]
        self.assertLess(sum(hunger[-4:]), 0.5 * sum(hunger[:4]) + 1e-9)
        self.assertGreater(min(record.memory.prices[key] for key in stale if key in record.memory.prices),
                           0.01 * setup.opening_prices[PORRIDGE])
        self.assertEqual(record.book.check_conservation(1e-6).breaches, ())


if __name__ == "__main__":
    unittest.main()
