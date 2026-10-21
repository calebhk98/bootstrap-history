"""Real figures are turned nominal with a level a few thin goods cannot move: a thin good's remembered ask spiking
must not raise the nominal leisure anchor wage, or wages raise costs and asks and the index rises again."""

QUICK_TOPIC = True

import unittest

from sim.economy import year_labour
from sim.economy.economy import Economy
from sim.economy.market_memory import MarketMemory
from sim.economy.year_close import remember_basket_price_level
from sim.tests import economy_fixture as fixture

THIN_GOOD_KEY = "metal_kg|town@b9"
SPIKE = 1.0e6


def spiked_economy():
    setup = fixture.stationary_setup()
    economy = Economy(setup)
    economy.step(fixture.quiet_year(setup))
    economy.record.leisure_anchor_wage = {fixture.LABOURER: 1.0}
    economy.record.memory.prices[THIN_GOOD_KEY] *= SPIKE
    remember_basket_price_level(setup, economy.record)
    return setup, economy


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
    def test_a_thin_good_spike_moves_the_reported_basket_level_but_not_the_nominal_anchor_wage(self):
        setup, economy = spiked_economy()
        view = economy.view()
        self.assertGreater(view.basket_price_level(setup.currency_id), 100.0)
        outside = year_labour.outside_option_by_tile(setup, economy.record, view)
        offers = year_labour.labour_offers(setup, economy.record, view, outside)
        supply = economy._hour_supply(offers, view, outside)
        self.assertAlmostEqual(supply.anchor_wage[fixture.LABOURER], view.chained_price_level(setup.currency_id))
        self.assertLess(supply.anchor_wage[fixture.LABOURER], 10.0)


if __name__ == "__main__":
    unittest.main()
