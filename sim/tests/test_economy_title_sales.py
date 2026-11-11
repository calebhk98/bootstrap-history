"""Complaint 538 and 641: titles change hands at a price. A holder short of cash offers hectares at what its rent is worth at the rate cash
costs it, buyers bid what the rent is worth at their own rate, a tile clears at one price between the two, and the price makes
the land yield lenders read (`lender_ask.land_yield`)."""

QUICK_TOPIC = True

import types
import unittest

from sim.book import Book
from sim.economy import lender_ask, title_sales, title_sales_year, titles
from sim.economy.credit_view import CreditView
from sim.economy.household_time_preference import HOUSEHOLD_TIME_PREFERENCE
from sim.economy.households_cohort import cohort_id, cohorts_for_tile
from sim.economy.market_memory import MarketMemory
from sim.economy.record import EconomyRecord
from sim.economy.types import CurrencySpec, TileSpec, Transfer

RENT = 4.0                  # money a hectare earns a year


class ValuationTests(unittest.TestCase):
    def test_a_holder_short_of_cash_discounts_at_the_rate_cash_costs_it(self):
        self.assertAlmostEqual(title_sales.seller_discount_rate(0.05, 0.20), 0.20)

    def test_a_holder_whose_cash_is_cheap_keeps_its_own_alternative(self):
        self.assertAlmostEqual(title_sales.seller_discount_rate(0.05, 0.03), 0.05)
        self.assertAlmostEqual(title_sales.seller_discount_rate(0.05, None), 0.05)

    def test_the_discount_rate_is_the_best_alternative_without_the_land_yield(self):
        self.assertAlmostEqual(title_sales.discount_rate(0.05, 0.02), 0.07)
        self.assertAlmostEqual(title_sales.discount_rate(0.05, 0.02, public_yield=0.09), 0.09)

    def test_an_offer_asks_the_rent_over_the_rate(self):
        offer = title_sales.asking_offer("seller", 10.0, RENT, 0.20)
        self.assertAlmostEqual(offer.lowest_price, 20.0)
        self.assertAlmostEqual(offer.hectares, 10.0)

    def test_a_holder_short_of_cash_offers_only_the_hectares_that_raise_it(self):
        offer = title_sales.asking_offer("seller", 10.0, RENT, 0.20, cash_needed=60.0)
        self.assertAlmostEqual(offer.hectares, 3.0)

    def test_no_rent_or_no_free_title_is_no_offer(self):
        self.assertIsNone(title_sales.asking_offer("seller", 10.0, 0.0, 0.20))
        self.assertIsNone(title_sales.asking_offer("seller", 0.0, RENT, 0.20))

    def test_a_bid_is_the_rent_over_the_buyers_rate_within_its_cash(self):
        bid = title_sales.bid_for("buyer", RENT, 0.05, 200.0)
        self.assertAlmostEqual(bid.highest_price, 80.0)
        self.assertAlmostEqual(bid.hectares, 2.5)
        self.assertIsNone(title_sales.bid_for("buyer", RENT, 0.05, 0.0))


class ClearingTests(unittest.TestCase):
    def test_a_cash_short_holder_sells_to_a_richer_buyer_at_a_price_between_their_valuations(self):
        seller = title_sales.asking_offer("seller", 10.0, RENT, 0.20, cash_needed=60.0)        # 20 a hectare, 3 hectares
        buyer = title_sales.bid_for("buyer", RENT, 0.05, 1000.0)                               # 80 a hectare
        sales = title_sales.clear_tile([seller], [buyer])
        self.assertEqual(len(sales), 1)
        self.assertEqual((sales[0].seller, sales[0].buyer), ("seller", "buyer"))
        self.assertAlmostEqual(sales[0].hectares, 3.0)
        self.assertTrue(seller.lowest_price <= sales[0].price_per_hectare <= buyer.highest_price)
        self.assertAlmostEqual(sales[0].price_per_hectare, 50.0)

    def test_no_sale_where_the_valuations_do_not_cross(self):
        seller = title_sales.asking_offer("seller", 10.0, RENT, 0.05)          # asks 80
        buyer = title_sales.bid_for("buyer", RENT, 0.20, 1000.0)               # bids 20
        self.assertEqual(title_sales.clear_tile([seller], [buyer]), [])

    def test_the_cheapest_sellers_meet_the_dearest_buyers_and_the_rest_stay_put(self):
        sellers = [title_sales.Seller("dear", 5.0, 70.0), title_sales.Seller("cheap", 5.0, 30.0)]
        buyers = [title_sales.Buyer("low", 5.0, 40.0), title_sales.Buyer("high", 5.0, 90.0)]
        sales = title_sales.clear_tile(sellers, buyers)
        self.assertEqual([(sale.seller, sale.buyer) for sale in sales], [("cheap", "high")])
        self.assertAlmostEqual(sales[0].price_per_hectare, 60.0)         # between the ask of 30 and the bid of 90

    def test_a_buyer_buys_no_more_than_it_wants(self):
        sales = title_sales.clear_tile([title_sales.Seller("seller", 10.0, 20.0)], [title_sales.Buyer("buyer", 2.0, 80.0)])
        self.assertAlmostEqual(sum(sale.hectares for sale in sales), 2.0)

    def test_proceeds_and_the_year_price_follow_the_sales(self):
        sales = [title_sales.Sale("a", "x", 2.0, 50.0), title_sales.Sale("b", "x", 6.0, 70.0)]
        self.assertAlmostEqual(title_sales.year_price(sales), 65.0)
        self.assertEqual(title_sales.proceeds(sales), {"a": 100.0, "b": 420.0})
        self.assertIsNone(title_sales.year_price([]))


class LandYieldTests(unittest.TestCase):
    def test_the_land_yield_is_the_rent_over_the_price_paid_weighted_by_hectares_sold(self):
        found = title_sales.market_land_yield({"a": 4.0, "b": 2.0, "c": 9.0}, {"a": 50.0, "b": 50.0, "c": 10.0},
                                              {"a": 1.0, "b": 1.0, "c": 0.0})
        self.assertAlmostEqual(found, 3.0 / 50.0)

    def test_without_a_sale_there_is_no_land_yield(self):
        self.assertIsNone(title_sales.market_land_yield({"a": 4.0}, {}, {}))

    def test_the_land_yield_reaches_the_lenders_ask(self):
        found = title_sales.market_land_yield({"a": 4.0}, {"a": 40.0}, {"a": 1.0})            # a tenth a year over the price
        plain = lender_ask.lowest_ask(HOUSEHOLD_TIME_PREFERENCE, 0.0)
        lifted = lender_ask.lowest_ask(HOUSEHOLD_TIME_PREFERENCE, 0.0, land_yield=found)
        self.assertGreater(lifted, plain)
        self.assertAlmostEqual(lifted, found)

    def test_the_view_gives_the_land_yield_for_its_own_currency_only(self):
        view = CreditView(MarketMemory(), Book(), types.SimpleNamespace(goods=lambda: ()), "coin", None, lambda tile: tile,
                          land_yield=lambda: 0.1)
        self.assertEqual(view.land_yield("coin"), 0.1)
        self.assertIsNone(view.land_yield("other"))


TILE = "t"
MONEY = "coin"
POOR, RICH = cohort_id(TILE, 0), cohort_id(TILE, 2)
COST_OF_CASH = 0.20


def _world(poor_cash: float, rich_cash: float, poor_target: float = 100.0):
    tile = TileSpec(TILE, 40.0, 10.0, 1.0, False, (), 1.0, 1.0)      # a hundred hectares
    setup = types.SimpleNamespace(currency_id=MONEY, tiles={TILE: tile}, opening_rate=0.05)
    record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec(MONEY, "fiat", None, 0.0, None))
    for cohort in cohorts_for_tile(TILE, 300.0, 0.5, 0.4, class_count=3):
        record.cohorts[cohort.agent_id] = type(cohort)(**{**vars(cohort), "cash_target": poor_target if cohort.agent_id == POOR else 0.0,
                                                           "expected_inflation": 0.0})
    record.land.titles = {TILE: {POOR: 0.5, RICH: 0.5}}
    record.land.land_rent = {TILE: RENT}
    if poor_cash > 0.0:
        record.book.transfer(Transfer("edge:legacy", POOR, MONEY, poor_cash, "opening"))
    if rich_cash > 0.0:
        record.book.transfer(Transfer("edge:legacy", RICH, MONEY, rich_cash, "opening"))
    return setup, record


class YearTests(unittest.TestCase):
    def test_a_holder_short_of_its_cash_target_sells_title_to_a_richer_neighbour(self):
        setup, record = _world(poor_cash=10.0, rich_cash=100000.0)
        before = (record.book.balance(POOR, MONEY), record.book.balance(RICH, MONEY))
        sales = title_sales_year.run(setup, record, None, COST_OF_CASH)
        self.assertTrue(sales)
        self.assertTrue(all(sale.seller == POOR and sale.buyer == RICH for sale in sales))
        self.assertLess(titles.holding(record, TILE, POOR), 0.5)
        self.assertAlmostEqual(titles.holding(record, TILE, RICH), 1.0 - titles.holding(record, TILE, POOR))
        paid = sum(sale.hectares * sale.price_per_hectare for sale in sales)
        self.assertAlmostEqual(record.book.balance(POOR, MONEY), before[0] + paid)
        self.assertAlmostEqual(record.book.balance(RICH, MONEY), before[1] - paid)
        self.assertAlmostEqual(record.land.sale_price_by_tile[TILE], title_sales.year_price(sales))

    def test_the_price_lies_between_the_sellers_and_the_buyers_valuations(self):
        setup, record = _world(poor_cash=10.0, rich_cash=100000.0)
        sales = title_sales_year.run(setup, record, None, COST_OF_CASH)
        asks, bids = RENT / COST_OF_CASH, RENT / title_sales.discount_rate(HOUSEHOLD_TIME_PREFERENCE, 0.0)
        self.assertTrue(asks <= sales[0].price_per_hectare <= bids)

    def test_the_seller_stays_on_the_land_as_the_buyers_tenant(self):
        setup, record = _world(poor_cash=10.0, rich_cash=100000.0)
        sales = title_sales_year.run(setup, record, None, COST_OF_CASH)
        sold_share = sum(sale.hectares for sale in sales) / 100.0
        self.assertAlmostEqual(titles.tenant_share(record, TILE, POOR), sold_share)

    def test_no_sale_when_nobody_is_short_of_cash(self):
        setup, record = _world(poor_cash=500.0, rich_cash=100000.0)
        self.assertEqual(title_sales_year.run(setup, record, None, COST_OF_CASH), [])
        self.assertEqual(record.land.sale_price_by_tile, {})

    def test_no_sale_when_no_buyer_has_cash(self):
        setup, record = _world(poor_cash=10.0, rich_cash=0.0)
        self.assertEqual(title_sales_year.run(setup, record, None, COST_OF_CASH), [])

    def test_no_sale_when_cash_costs_the_holder_no_more_than_the_buyer_discounts_at(self):
        setup, record = _world(poor_cash=10.0, rich_cash=100000.0)
        self.assertEqual(title_sales_year.run(setup, record, None, 0.01), [])

    def test_a_pledged_title_is_not_for_sale(self):
        setup, record = _world(poor_cash=10.0, rich_cash=100000.0)
        self.assertEqual(title_sales_year.run(setup, record, None, COST_OF_CASH, pledges={(POOR, TILE): 0.5}), [])

    def test_the_year_sets_the_land_yield_lenders_read_from_the_price(self):
        setup, record = _world(poor_cash=10.0, rich_cash=100000.0)
        self.assertIsNone(record.credit.land_yield)
        title_sales_year.run(setup, record, None, COST_OF_CASH)
        self.assertAlmostEqual(record.credit.land_yield, RENT / record.land.sale_price_by_tile[TILE])

    def test_a_year_without_a_sale_keeps_the_land_yield_last_read(self):
        setup, record = _world(poor_cash=500.0, rich_cash=100000.0)
        record.credit.set_land_yield(0.07)
        title_sales_year.run(setup, record, None, COST_OF_CASH)
        self.assertEqual(record.credit.land_yield, 0.07)


if __name__ == "__main__":
    unittest.main()
