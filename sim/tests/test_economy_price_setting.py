"""Complaint 473: a seller sets its ask for the year as Eurace@Unibi's Firm_set_price does (price_setting.py): the
price on a grid around its own that earns most, from the market's size times the share a logit gives it against the
other sellers' asks, with sales capped by the stock it holds."""

QUICK_TOPIC = True

import unittest

from sim.economy import price_setting

UNIT_COST = 1.0
MARKET_SIZE = 100.0
STOCK = 1000.0       # more than any share of the market buys


def choose(current=1.0, rivals=((1.125, 1.0),) * 3, stock=STOCK, intensity=price_setting.LOGIT_INTENSITY, floor=0.0,
           ceiling=10.0):
    return price_setting.best_price(current, UNIT_COST, MARKET_SIZE, list(rivals), stock, floor, ceiling, intensity)


class LogitShareTests(unittest.TestCase):
    def test_a_lone_seller_has_the_whole_market(self):
        self.assertEqual(price_setting.logit_share(1.0, [], 12.0), 1.0)

    def test_equal_prices_split_the_market_equally(self):
        self.assertAlmostEqual(price_setting.logit_share(1.0, [(1.0, 1.0)] * 3, 12.0), 0.25)

    def test_a_rival_standing_for_two_workshops_counts_twice(self):
        self.assertAlmostEqual(price_setting.logit_share(1.0, [(1.0, 2.0)], 12.0), 1.0 / 3.0)

    def test_a_dearer_ask_has_a_smaller_share(self):
        self.assertLess(price_setting.logit_share(1.2, [(1.0, 1.0)], 12.0), price_setting.logit_share(1.0, [(1.0, 1.0)], 12.0))


class GridTests(unittest.TestCase):
    def test_the_grid_holds_the_current_price_and_stays_in_its_span(self):
        grid = price_setting.grid_prices(10.0)
        self.assertIn(10.0, [round(each, 9) for each in grid])
        self.assertAlmostEqual(min(grid), 10.0 * price_setting.GRID_START)
        self.assertLess(max(grid), 10.0 * price_setting.GRID_END)


class BestPriceTests(unittest.TestCase):
    def test_equal_competitors_give_cost_plus_the_logit_markup(self):
        # three rivals at the symmetric answer: share 1/4, markup = intensity * (1 - share) / (intensity * (1 - share) - 1)
        markup = 12.0 * 0.75 / (12.0 * 0.75 - 1.0)
        self.assertAlmostEqual(choose(), UNIT_COST * markup, delta=0.02)

    def test_a_sharper_logit_lowers_the_price(self):
        self.assertLess(choose(intensity=24.0), choose(intensity=12.0))

    def test_a_seller_with_no_stock_keeps_its_price(self):
        self.assertEqual(choose(current=1.3, stock=0.0), 1.3)

    def test_a_seller_that_would_sell_out_raises_to_the_price_that_just_sells_out(self):
        scarce = choose(stock=5.0)       # a quarter share of 100 sells 25 units at the logit price, so the stock binds
        self.assertGreater(scarce, choose())

    def test_the_price_stays_inside_the_bounds(self):
        self.assertEqual(choose(floor=1.2, ceiling=1.3), 1.2)
        self.assertEqual(choose(rivals=(), ceiling=1.1), 1.1)


if __name__ == "__main__":
    unittest.main()
