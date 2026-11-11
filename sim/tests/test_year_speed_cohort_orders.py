"""Numba port, the year's cohort orders: `households_orders_pack.kernel_orders` (every cohort ordered in one kernel call) agrees with
the old per-cohort path (`households.goods_orders`, then `year_goods.less_what_it_grew`, which stays the path for a basket the kernel does
not cover) on random cohorts, baskets, prices, holdings, claims, plots and cash; no game.

The kernel sums exactly where the old code used `math.fsum`, so which bids exist agrees; what is left is the order of a few plain sums and
`pow`, so figures agree to a relative tolerance and not always bit for bit. The old path has discrete rules (a bid exists when its budget is
above nothing) and can jump under a one-ulp nudge of its cash: a case where it does is no test of the kernel and is skipped
(`is_stable`), and most cases must be compared."""

QUICK_TOPIC = True

import dataclasses
import random
import unittest

from sim.book import Book
from sim.book_types import GoodsMove
from sim.economy import households, households_orders_pack
from sim.economy.goods_order_book import GoodsOrderBook
from sim.economy.goods_order_tables import HOUSEHOLD
from sim.economy.market_tables import MarketTables
from sim.economy.types import EDGE_PRODUCTION
from sim.economy.households_cohort import Cohort
from sim.economy.year_goods import less_what_it_grew
from sim.tests.test_opening_demand_kernel import SPECS, View, random_units, random_world
from sim.world import need_basket

TOLERANCE = 1e-9


class YearView(View):
    """The opening test's view with the holdings of gold and tools, the lending claims and equity the year's orders read."""

    def __init__(self, prices, held, rate, claims, equity):
        super().__init__(prices, held, rate)
        self.claims_of, self.equity_of = claims, equity

    def claims(self, agent, currency):
        return self.claims_of.get(agent, 0.0)

    def equity(self, agent):
        return self.equity_of.get(agent, 0.0)

    def loss_rate(self, agent, currency):
        return 0.01

    def land_yield(self, currency):
        return None

    def public_yield(self, currency):
        return None


def year_world(rng):
    basket, view, cohorts = random_world(rng)
    held = dict(view.held)
    claims, equity = {}, {}
    for cohort in cohorts:
        income = cohort.last_year_income
        if rng.random() < 0.6:
            held[(cohort.agent_id, "gold")] = rng.uniform(0.0, 0.2)
        if rng.random() < 0.4:
            held[(cohort.agent_id, "hoe")] = rng.uniform(0.0, 60.0)
        claims[cohort.agent_id] = rng.choice([0.0, income * rng.uniform(0.0, 3.0)])
        equity[cohort.agent_id] = rng.choice([0.0, income * rng.uniform(0.0, 5.0)])
    return basket, YearView(view.prices, held, view.rate, claims, equity), cohorts


def reference(cohort, basket, priced, view, cash, income, grown, smooth_rise):
    orders = households.goods_orders(cohort, view, cash, income, basket, SPECS, priced, smooth_rise=smooth_rise, shared_store={})
    return less_what_it_grew(orders, cohort, basket, grown)


def kernel(cohorts, baskets, priceds, view, cashes, incomes, grown, smooth_rise):
    entries = [(cohort, basket, priced, cash, income, units) for cohort, basket, priced, cash, income, units
               in zip(cohorts, baskets, priceds, cashes, incomes, grown)]
    """The cohorts' orders with the bids read back from the rows the kernel wrote."""
    book = Book()
    book.post((), [GoodsMove(EDGE_PRODUCTION, cohort.agent_id, good, cohort.tile, quantity, "test holding")
                   for cohort in cohorts for (agent, good), quantity in sorted(view.held.items())
                   if agent == cohort.agent_id and quantity > 0.0])     # the view's holdings are the book's: the kernel reads the book in a block
    orders = GoodsOrderBook(book, MarketTables())
    made, rows, planned = households_orders_pack.kernel_orders(
        view, SPECS, entries, smooth_rise, lambda cohort: (cohort.tile, cohort.hired_work_per_person),
        lambda cohort: stores.setdefault((cohort.tile, cohort.hired_work_per_person), {}), orders)
    if rows is not None:
        orders.append_bids(*rows, HOUSEHOLD)
    bids = orders.bids_of(range(orders.bid_count()))
    return {agent: dataclasses.replace(each, bids=tuple(bid for bid in bids if bid.buyer == agent)) for agent, each in made.items()}, planned


stores = {}


def same_bids(test, got, expected):
    test.assertEqual([(bid.good, bid.area, bid.tile, bid.priority) for bid in got],
                     [(bid.good, bid.area, bid.tile, bid.priority) for bid in expected])
    for left, right in zip(got, expected):
        for field in ("floor_quantity", "flexible_quantity", "reference_price", "elasticity", "budget", "maximum_price"):
            test.assertAlmostEqual(getattr(left, field), getattr(right, field), delta=TOLERANCE * max(1.0, abs(getattr(right, field))) if getattr(right, field) != float("inf") else 0.0,
                                   msg="%s %s" % (left.good, field))


def same_orders(test, got, expected):
    same_bids(test, got.bids, expected.bids)
    test.assertEqual([(offer.good, offer.area, offer.tile) for offer in got.offers], [(offer.good, offer.area, offer.tile) for offer in expected.offers])
    for left, right in zip(got.offers, expected.offers):
        test.assertAlmostEqual(left.quantity, right.quantity, delta=TOLERANCE * max(1.0, right.quantity))
        test.assertAlmostEqual(left.reservation_price, right.reservation_price, delta=TOLERANCE * max(1.0, right.reservation_price))
    test.assertEqual(len(got.funds_offers), len(expected.funds_offers))
    for left, right in zip(got.funds_offers, expected.funds_offers):
        test.assertAlmostEqual(left.amount, right.amount, delta=TOLERANCE * max(1.0, right.amount))
        test.assertAlmostEqual(left.minimum_rate, right.minimum_rate, delta=TOLERANCE)


def is_stable(cohort, basket, priced, view, cash, income, grown, smooth_rise, expected):
    nudged = reference(cohort, basket, priced, view, cash * (1.0 + 1e-12), income, grown, smooth_rise)
    return ([bid.good for bid in nudged.bids] == [bid.good for bid in expected.bids]
            and len(nudged.offers) == len(expected.offers) and len(nudged.funds_offers) == len(expected.funds_offers))


class CohortOrdersAgreeTests(unittest.TestCase):
    def test_kernel_and_old_path_agree_on_random_cohorts(self):
        rng = random.Random(5)
        compared = skipped = with_store = with_offers = with_funds = 0
        for _case in range(80):
            basket, view, cohorts = year_world(rng)
            stores.clear()
            smooth_rise = rng.random() < 0.8
            units = random_units(rng, cohorts, basket)
            priceds = [households.need_prices(basket, view, cohort.tile) for cohort in cohorts]
            cashes = [cohort.last_year_income * rng.uniform(0.3, 2.5) for cohort in cohorts]
            incomes = [cohort.last_year_income * rng.uniform(0.5, 1.5) for cohort in cohorts]
            cohorts = [dataclasses.replace(cohort, last_year_income=cohort.last_year_income * rng.choice([0.0, 1.0])) for cohort in cohorts]
            got, planned = kernel(cohorts, [basket] * len(cohorts), priceds, view, cashes, incomes, [units[cohort.agent_id] for cohort in cohorts], smooth_rise)
            for cohort, priced, cash, income in zip(cohorts, priceds, cashes, incomes):
                grown = units[cohort.agent_id]
                expected = reference(cohort, basket, priced, view, cash, income, grown, smooth_rise)
                if not is_stable(cohort, basket, priced, view, cash, income, grown, smooth_rise, expected):
                    skipped += 1
                    continue
                same_orders(self, got[cohort.agent_id], expected)
                self.assertAlmostEqual(planned[cohort.agent_id], sum(bid.budget for bid in expected.bids), delta=1e-6)
                compared += 1
                with_store += any(bid.floor_quantity == 0.0 and bid.priority == 2 for bid in expected.bids)
                with_offers += bool(expected.offers)
                with_funds += bool(expected.funds_offers)
        self.assertGreaterEqual(compared, 0.8 * (compared + skipped), "most cases are compared (%d skipped)" % skipped)
        self.assertGreater(with_store, 5, "the store bids are exercised")
        self.assertGreater(with_funds, 20, "the savings offers are exercised")
        self.assertGreater(with_offers, 0, "the store's offers are exercised")

    def test_a_cohort_without_people_orders_nothing(self):
        rng = random.Random(3)
        basket, view, cohorts = year_world(rng)
        stores.clear()
        empty = dataclasses.replace(cohorts[0], people=0.0)
        priced = households.need_prices(basket, view, empty.tile)
        got, _planned = kernel([empty], [basket], [priced], view, [100.0], [10.0], [{}], True)
        self.assertEqual(got[empty.agent_id].bids, ())
        self.assertEqual(got[empty.agent_id].funds_offers, ())

    def test_no_cohorts_gives_no_orders(self):
        orders = GoodsOrderBook(Book(), MarketTables())
        self.assertEqual(households_orders_pack.kernel_orders(year_world(random.Random(1))[1], SPECS, [], True, lambda cohort: None,
                                                              lambda cohort: {}, orders), ({}, None, {}))


if __name__ == "__main__":
    unittest.main()
