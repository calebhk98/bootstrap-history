"""A sale is paid at the price on the acting tile falling as the year's sales add to what is offered there: `GoodsPricing._climb`
reads the economy's response along the order, and `sale_proceeds` multiplies the tile price by it."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.goods_market_pricing import GoodsPricing

TILE = (3, 4)
GOOD = "iron"
TILE_PRICE = 100.0


class Economy:
    """A book whose price factor falls linearly with the tonnes offered, down to a floor; every call is recorded."""

    def __init__(self, fall_per_tonne, offered=None):
        self.fall_per_tonne = fall_per_tonne
        self.offered = offered
        self.calls = []

    def acting_tile(self):
        return TILE

    def agent_offered_tonnes(self, good, tile):
        return self.offered

    def agent_price_response(self, good, extra_offered, extra_demanded, tile):
        self.calls.append((extra_offered, extra_demanded))
        return max(0.2, 1.0 - self.fall_per_tonne * (extra_offered - extra_demanded))


class Market(GoodsPricing):
    def __init__(self, economy, traded=True):
        self._sim = SimpleNamespace(economy=economy)
        self.traded = traded

    def _economy_good(self, material):
        return GOOD if self.traded else None

    def price_at_tile_per_tonne(self, material):
        return TILE_PRICE


class SaleClimbTests(unittest.TestCase):
    def test_a_sale_is_paid_less_per_tonne_the_more_is_sold(self):
        market = Market(Economy(fall_per_tonne=0.01))
        _money, small = market.sale_proceeds("iron", 1.0)
        _money, big = market.sale_proceeds("iron", 40.0)
        self.assertLess(big, small)

    def test_a_sale_is_paid_no_less_than_the_price_after_all_of_it_is_on_offer(self):
        economy = Market(Economy(fall_per_tonne=0.01))._sim.economy
        market = Market(economy)
        _money, mean = market.sale_proceeds("iron", 40.0)
        self.assertGreaterEqual(mean, TILE_PRICE * economy.agent_price_response(GOOD, 40.0, 0.0, TILE))

    def test_a_sale_is_paid_no_more_than_the_first_tonne(self):
        market = Market(Economy(fall_per_tonne=0.01))
        _money, small = market.sale_proceeds("iron", 1.0)
        _money, big = market.sale_proceeds("iron", 40.0)
        self.assertLessEqual(big, small * (1.0 + 1e-9))

    def test_where_the_economys_sellers_give_way_a_sale_keeps_the_price(self):
        market = Market(Economy(fall_per_tonne=0.0))
        money, mean = market.sale_proceeds("iron", 40.0)
        self.assertAlmostEqual(mean, TILE_PRICE)
        self.assertAlmostEqual(money, TILE_PRICE * 40.0)

    def test_the_sale_adds_to_what_is_offered_and_does_not_draw_on_demand(self):
        economy = Economy(fall_per_tonne=0.01)
        Market(economy).sale_proceeds("iron", 40.0, already=10.0)
        self.assertTrue(economy.calls)
        self.assertTrue(all(offered >= 10.0 and demanded == 0.0 for offered, demanded in economy.calls))

    def test_sales_already_made_this_year_lower_the_price_of_the_next(self):
        market = Market(Economy(fall_per_tonne=0.01))
        _money, fresh = market.sale_proceeds("iron", 5.0, already=0.0)
        _money, later = market.sale_proceeds("iron", 5.0, already=30.0)
        self.assertLess(later, fresh)

    def test_a_good_the_economy_has_no_book_for_sells_at_the_tile_price(self):
        market = Market(Economy(fall_per_tonne=0.5), traded=False)
        self.assertEqual(market.sale_proceeds("iron", 40.0), (TILE_PRICE * 40.0, TILE_PRICE))


if __name__ == "__main__":
    unittest.main()
