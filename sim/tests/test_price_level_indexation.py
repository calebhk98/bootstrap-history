"""Real figures are turned nominal with a level a few thin goods cannot move: a thin good's remembered ask spiking
must not raise the nominal leisure anchor wage, or wages raise costs and asks and the index rises again."""

QUICK_TOPIC = True

import unittest

from sim.economy.market_memory import MarketMemory


class ChainedLevelTests(unittest.TestCase):
    def test_a_median_year_chains_the_level_whatever_the_fixed_basket_does(self):
        memory = MarketMemory()
        memory.note_basket_price_level("coin", 5000.0, observed_inflation=0.1)
        memory.note_basket_price_level("coin", 9.0e9, observed_inflation=0.1)
        self.assertAlmostEqual(memory.price_levels["coin"], 1.21)
        self.assertEqual(memory.basket_price_levels["coin"], 9.0e9)

    def test_a_year_when_the_median_price_fell_to_nothing_keeps_a_positive_level(self):
        memory = MarketMemory()
        memory.note_basket_price_level("coin", 1.0, observed_inflation=-1.0)
        self.assertGreater(memory.price_levels["coin"], 0.0)


class IndexationTests(unittest.TestCase):
    def test_a_thin_good_spike_moves_the_reported_basket_level_but_not_the_chained_one(self):
        memory = MarketMemory()
        memory.note_basket_price_level("coin", 1.0e6, observed_inflation=0.0)
        self.assertEqual(memory.basket_price_levels["coin"], 1.0e6)
        self.assertEqual(memory.price_levels["coin"], 1.0)


if __name__ == "__main__":
    unittest.main()
