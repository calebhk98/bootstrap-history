"""Eurace's household portfolio decision and the clearing house's matching of share orders (household_portfolio.py),
and the buy cap on a new issue that hands the result to the share market (shares.bids_from)."""

QUICK_TOPIC = True

import unittest

from types import SimpleNamespace

from sim.book import Book
from sim.economy import household_portfolio as portfolio, portfolio_year, shares
from sim.economy.types import FundsOffer, Transfer


class FractionToInvestTests(unittest.TestCase):
    def test_equal_returns_split_the_budget_in_half(self):
        self.assertAlmostEqual(portfolio.fraction_to_invest(0.05, 0.05, 3.0), 0.5)

    def test_a_dearer_share_return_raises_the_fraction_and_a_poorer_one_cuts_it(self):
        self.assertGreater(portfolio.fraction_to_invest(0.05, 0.10, 3.0), 0.5)
        self.assertLess(portfolio.fraction_to_invest(0.05, 0.02, 3.0), 0.5)

    def test_no_positive_performance_gives_no_fraction(self):
        self.assertIsNone(portfolio.fraction_to_invest(0.0, 0.0, 3.0))


class NetInvestmentTests(unittest.TestCase):
    def test_below_the_target_it_buys_the_difference(self):
        self.assertAlmostEqual(portfolio.net_investment(0.5, 300.0, 100.0), 100.0)

    def test_above_the_target_it_sells_the_difference(self):
        self.assertAlmostEqual(portfolio.net_investment(0.5, 100.0, 300.0), -100.0)

    def test_it_cannot_sell_more_than_it_holds_nor_buy_more_than_its_savings(self):
        self.assertAlmostEqual(portfolio.net_investment(0.0, 100.0, 300.0), -300.0)
        self.assertAlmostEqual(portfolio.net_investment(1.0, 50.0, 0.0), 50.0)


class MatchOrdersTests(unittest.TestCase):
    def test_when_buyers_are_the_long_side_each_buyer_gets_the_short_sides_share(self):
        matched, ratio = portfolio.match_orders({"a": 20.0, "b": 10.0, "c": -10.0})
        self.assertAlmostEqual(ratio, 3.0)
        self.assertAlmostEqual(matched["a"], 20.0 / 3.0)
        self.assertAlmostEqual(matched["b"], 10.0 / 3.0)
        self.assertAlmostEqual(matched["c"], -10.0)

    def test_when_sellers_are_the_long_side_each_seller_sells_the_ratio_of_its_order(self):
        matched, ratio = portfolio.match_orders({"a": 10.0, "b": -30.0, "c": -10.0})
        self.assertAlmostEqual(ratio, 0.25)
        self.assertAlmostEqual(matched["b"], -7.5)
        self.assertAlmostEqual(matched["a"], 10.0)

    def test_with_no_seller_nothing_trades_and_the_ratio_is_one(self):
        matched, ratio = portfolio.match_orders({"a": 20.0})
        self.assertEqual(matched, {"a": 0.0})
        self.assertEqual(ratio, 1.0)


class IndexPriceTests(unittest.TestCase):
    def test_the_price_follows_the_demand_supply_ratio_within_the_bounds(self):
        self.assertAlmostEqual(portfolio.next_price_factor(1.0, 1.05, 1.0, 1.1, 0.9), 1.05)

    def test_a_ratio_beyond_the_bounds_moves_it_by_the_bound(self):
        self.assertAlmostEqual(portfolio.next_price_factor(2.0, 4.0, 1.0, 1.1, 0.9), 2.2)
        self.assertAlmostEqual(portfolio.next_price_factor(2.0, 0.25, 1.0, 1.1, 0.9), 1.8)


class WealthAtIndexTests(unittest.TestCase):
    def test_bought_parts_are_worth_the_index_factor_times_the_producers_worth(self):
        self.assertAlmostEqual(portfolio.share_wealth({"farm": 0.25, "mine": 0.5}, {"farm": 400.0, "mine": 100.0}, 0.9),
                               0.9 * (0.25 * 400.0 + 0.5 * 100.0))

    def test_the_expected_yield_is_dividends_over_the_index_value(self):
        self.assertAlmostEqual(portfolio.expected_yield({"farm": 10.0, "mine": 5.0}, {"farm": 400.0, "mine": 100.0}), 0.03)

    def test_with_no_index_value_there_is_no_yield(self):
        self.assertIsNone(portfolio.expected_yield({"farm": 10.0}, {}))


class BuyCapTests(unittest.TestCase):
    def test_a_savers_bid_is_held_to_its_portfolio_buy_order(self):
        record = type("Record", (), {"cohorts": {"h": None}})()
        bids = shares.bids_from(record, [FundsOffer("h", "coin", 100.0, 0.05)], {}, {"h": 30.0})
        self.assertAlmostEqual(bids[0].funds, 30.0)

    def test_a_saver_without_an_order_is_not_capped(self):
        record = type("Record", (), {"cohorts": {"h": None}})()
        bids = shares.bids_from(record, [FundsOffer("h", "coin", 100.0, 0.05)], {}, {})
        self.assertAlmostEqual(bids[0].funds, 100.0)


class ApplyMatchesTests(unittest.TestCase):
    def test_a_seller_hands_its_matched_part_to_the_buyer_for_the_matched_value(self):
        book = Book()
        book.transfer(Transfer("edge:mint", "buyer", "coin", 100.0, "opening"))
        record = SimpleNamespace(book=book, shares={"farm": {"seller": 0.5}})
        portfolio_year.apply_matches(record, "coin", {"seller": -40.0, "buyer": 40.0}, {"seller": 200.0})
        self.assertAlmostEqual(record.shares["farm"]["seller"], 0.4)
        self.assertAlmostEqual(record.shares["farm"]["buyer"], 0.1)
        self.assertAlmostEqual(book.balance("seller", "coin"), 40.0)
        self.assertAlmostEqual(book.balance("buyer", "coin"), 60.0)


if __name__ == "__main__":
    unittest.main()
