"""A producer judges expanding at the price expected once its own additions are on the market (Complaint 336):
the residual price is read off the buyers' schedules, and a growth that pays at today's price but not at the
price it leaves is not asked a loan for."""

QUICK_TOPIC = True

import unittest

from sim.economy import expansion_price, producers_close
from sim.economy.types import Bid
from sim.tests.test_economy_producers import SMELT, View, farmer

GOOD, AREA, TILE = "metal", "area", "tile"


def buyers(elasticity=2.0):
    """One buyer whose want falls with the price: flexible demand around a reference price of one."""
    return [Bid("buyer", GOOD, AREA, TILE, 0.0, 100.0, 1.0, elasticity, 1e9)]


class PriceShareTests(unittest.TestCase):
    def test_nothing_added_leaves_the_price(self):
        self.assertEqual(expansion_price.share_after_addition(buyers(), GOOD, AREA, 100.0, 0.0), 1.0)

    def test_adding_output_lowers_the_price_more_the_more_is_added(self):
        small = expansion_price.share_after_addition(buyers(), GOOD, AREA, 100.0, 10.0)
        large = expansion_price.share_after_addition(buyers(), GOOD, AREA, 100.0, 50.0)
        self.assertLess(small, 1.0)
        self.assertLess(large, small)

    def test_steeper_demand_loses_more_price_for_the_same_addition(self):
        flat = expansion_price.share_after_addition(buyers(4.0), GOOD, AREA, 100.0, 20.0)
        steep = expansion_price.share_after_addition(buyers(1.0), GOOD, AREA, 100.0, 20.0)
        self.assertLess(steep, flat)

    def test_a_market_with_no_book_or_no_trade_shows_no_price_to_move(self):
        self.assertEqual(expansion_price.share_after_addition([], GOOD, AREA, 100.0, 10.0), 1.0)
        self.assertEqual(expansion_price.share_after_addition(buyers(), GOOD, AREA, 0.0, 10.0), 1.0)

    def test_the_producers_market_is_found_by_its_tile(self):
        share = expansion_price.price_share_of({(GOOD, AREA): buyers()}, {(GOOD, AREA): 100.0},
                                               lambda good, tile: AREA, TILE)
        self.assertLess(share(GOOD, 30.0), 1.0)
        self.assertEqual(share("other", 30.0), 1.0)


class ExpansionTests(unittest.TestCase):
    def view(self):
        return View({"metal": 20.0, "silver": 5.0, "ore": 1.0, "stone": 1.0}, {"smith": 1.0})

    def close(self, price_share=None):
        return producers_close.close_year(farmer(recipe_id="smelt"), SMELT, 500.0, 50.0, self.view(), None,
                                          price_share)

    def test_without_a_book_it_expands_at_the_price_it_sees(self):
        self.assertIsNotNone(self.close().loan_request)

    def test_growth_that_leaves_the_price_above_the_rate_is_still_financed(self):
        self.assertIsNotNone(self.close(lambda good, added: 0.95).loan_request)

    def test_growth_that_pays_at_todays_price_but_not_at_the_price_it_leaves_is_not(self):
        self.assertIsNone(self.close(lambda good, added: 0.01).loan_request)
        self.assertEqual(self.close(lambda good, added: 0.01).expansion_runs, 0.0)

    def test_the_addition_priced_is_the_expansions_own_output(self):
        asked = []

        def share(good, added):
            asked.append((good, added))
            return 1.0
        result = self.close(share)
        self.assertIn(("metal", result.expansion_runs * SMELT.outputs["metal"]), asked)


if __name__ == "__main__":
    unittest.main()
