"""A market with buyers and no maker: a newcomer comes whenever the bids would take its output at the
entry price, even where the market remembers a price too low to pay."""

QUICK_TOPIC = True

import unittest

from sim.economy.economy import Economy
from sim.tests import economy_fixture as fixture


class StalePriceScenarioTests(unittest.TestCase):
    def test_makers_return_to_a_market_whose_remembered_price_was_left_too_low(self):
        setup = fixture.small_setup()
        economy = Economy(setup)
        record = economy.record
        for producer_id in [key for key, producer in record.producers.items() if producer.recipe_id == fixture.FARM]:
            del record.producers[producer_id]
        for key in [key for key in record.memory.prices if key.startswith(fixture.GRAIN)]:
            record.memory.prices[key] *= 0.01
        for _year in range(12):
            economy.step(fixture.quiet_year(setup))
        farms = [producer for producer in record.producers.values() if producer.recipe_id == fixture.FARM]
        self.assertTrue(farms)
        self.assertEqual(record.book.check_conservation(1e-6).breaches, ())


if __name__ == "__main__":
    unittest.main()
