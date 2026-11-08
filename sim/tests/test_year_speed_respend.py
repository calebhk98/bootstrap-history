"""Numba port, households' respend: the rounds run by the kernel (`goods_respend_year.respend`) leave the book, the year ledger and
every market as the per-buyer, per-market Python rounds they replaced (respend_reference.respend_plain) do, on random small
economies whose first round was cleared and settled the old way. No game.

A tolerance of one part in a million of the largest figure is needed because the kernel sums left to right where the old path used
`math.fsum`, and the rounds' postings are summed per good. The rounds' tail is discrete: a buyer that receives a quantity, or is
rationed of money, near rounding noise (1e-17 of a unit, or exactly none) goes on to bid or not, and its next bids move with it. A
case that differs, where either path moves by more than the tolerance when every first-round budget, offer and ask is nudged by one
part in 10^12, is not compared, and nine in ten must be.
"""

QUICK_TOPIC = True

import random
from collections.abc import Mapping
import unittest
from types import SimpleNamespace

from sim.book import Book
from sim.economy import goods_market, goods_respend, goods_respend_year, settlement
from sim.economy.goods_market_rows import MarketRows
from sim.economy.goods_order_book import GoodsOrderBook
from sim.economy.goods_table_views import LazyObjects
from sim.economy.market_tables import MarketTables
from sim.economy.entry import wanted_in_round
from sim.economy.goods_market_fills import sold_by_seller_tile
from sim.economy.households_cohort import Cohort
from sim.economy.types import Bid, EDGE_EXTERNAL, EDGE_MINT, EDGE_PRODUCTION, GoodsMove, Offer, Transfer
from sim.economy.year_ledger import YearLedger
from sim.world.need_basket import Basket, NeedSpec

from . import respend_reference

TOLERANCE = 1e-6
GOODS = ["bread", "fish", "oil", "cloth", "salt"]
TILES = ["t0", "t1", "t2", "t3"]


def baskets():
    one = Basket(needs=(NeedSpec("food", 1.0, 2.0, (("bread", 1.0), ("fish", 1.5), ("salt", 0.5)),
                                 share_limits=(("fish", 0.4),)),
                        NeedSpec("clothing", 0.0, 1.0, (("cloth", 1.0),)),
                        NeedSpec("light", 0.0, 1.5, (("oil", 1.0),))), substitution=2.0, need_data={})
    two = Basket(needs=(NeedSpec("food", 1.0, 2.0, (("bread", 1.0), ("fish", 2.0))),
                        NeedSpec("light", 0.0, 1.0, (("oil", 1.0), ("cloth", 0.2)))), substitution=1.3, need_data={})
    return [one, two]


class View:
    def area_of(self, good, tile):
        return "north" if tile in ("t0", "t1") or good == "salt" else "south"


def build(seed):
    """One random economy with its first round cleared and settled: (setup, record, view, ledger, markets, basket_of)."""
    rng = random.Random(seed)
    book = Book()
    view = View()
    cohorts = {}
    for index in range(rng.randint(2, 9)):
        name = "h%02d" % index
        cohorts[name] = Cohort(name, rng.choice(TILES), 0, 100.0, 50.0, 0.1)
        book.transfer(Transfer(EDGE_MINT, name, "coin", rng.choice([5.0, 60.0, 400.0, 3000.0]), "start"))
    sellers = ["p%d" % index for index in range(rng.randint(1, 5))] + ["merchant"]
    for name in sellers:
        book.transfer(Transfer(EDGE_MINT, name, "coin", rng.choice([0.0, 50.0, 800.0]), "start"))
    offers_by_market, bids_by_market = {}, {}
    for good in GOODS:
        for tile in TILES:
            area = view.area_of(good, tile)
            for seller in rng.sample(sellers, rng.randint(0, min(3, len(sellers)))):
                quantity = rng.choice([1.0, 8.0, 40.0, 200.0])
                book.move(GoodsMove(EDGE_PRODUCTION, seller, good, tile, quantity * rng.choice([1.0, 1.0, 0.5]), "make"))
                offers_by_market.setdefault((good, area), []).append(
                    Offer(seller, good, area, tile, quantity, rng.choice([0.4, 1.0, 2.5, 6.0, 0.0])))
    if rng.random() < 0.4:
        book.transfer(Transfer(EDGE_MINT, EDGE_EXTERNAL + ":far", "coin", 0.0, "start"))
        offers_by_market.setdefault(("oil", "north"), []).append(Offer(EDGE_EXTERNAL + ":far", "oil", "north", "t0", 300.0, 3.0))
    for name, cohort in cohorts.items():
        for good in GOODS:
            if rng.random() < 0.55:
                bids_by_market.setdefault((good, view.area_of(good, cohort.tile)), []).append(Bid(
                    name, good, view.area_of(good, cohort.tile), cohort.tile, rng.choice([0.0, rng.uniform(0.0, 20.0)]),
                    rng.choice([0.0, rng.uniform(0.0, 40.0)]), rng.uniform(0.5, 5.0), rng.choice([0.5, 1.0, 2.0]),
                    rng.choice([rng.uniform(5.0, 80.0), rng.uniform(80.0, 900.0)]), 0,
                    maximum_price=rng.choice([float("inf"), float("inf"), rng.uniform(1.0, 6.0)])))
    for key in list(offers_by_market):
        if rng.random() < 0.15:
            bids_by_market.setdefault(key, []).append(Bid("merchant", key[0], key[1], "t0", 0.0, 5.0, 2.0, 1.0, 40.0, 0))
    ledger = YearLedger()
    if rng.random() < 0.3:
        ledger.import_accounts = frozenset([sellers[0]])
    record = SimpleNamespace(cohorts=cohorts, book=book)
    setup = SimpleNamespace(currency_id="coin")
    markets = {}
    for key in sorted(set(offers_by_market) | set(bids_by_market)):
        bids, offers = bids_by_market.get(key, []), offers_by_market.get(key, [])
        last_price = rng.choice([None, 1.5, 3.0])
        result = goods_market.clear(bids, offers, key[0], key[1], "coin", last_price)
        delivered, bought = 0.0, {}
        if result.quantity > 0.0:
            done = settlement.settle_goods(book, result, ledger.import_accounts, ledger.export_accounts)
            bought, delivered = done.bought_by_buyer(), done.delivered
            ledger.note_settlement(done, "sales")
        ledger.note_clearing(result, delivered)
        markets[key] = goods_respend_year.LeftMarket(
            bids, result, goods_respend.offers_left(offers, sold_by_seller_tile(result.fills)), last_price, delivered,
            wanted_in_round(bids, offers, result), 0, bought)
    shared = baskets()
    return setup, record, view, ledger, markets, (lambda cohort: shared[int(cohort.agent_id[1:]) % 2])


def nudged(markets, factor):
    """The markets with every first-round bid's budget and every offer left scaled by `factor`, and their asks by its cube."""
    for market in markets.values():
        market.bids = [Bid(bid.buyer, bid.good, bid.area, bid.tile, bid.floor_quantity, bid.flexible_quantity,
                           bid.reference_price, bid.elasticity, bid.budget * factor, bid.priority,
                           maximum_price=bid.maximum_price) for bid in market.bids]
        market.all_bids = list(market.bids)
        market.offers = [Offer(offer.seller, offer.good, offer.area, offer.tile, offer.quantity * factor,
                               offer.reservation_price * factor ** 3) for offer in market.offers]


def snapshot(book):
    record = book.to_record()
    return {"money": record["money"], "goods": record["goods"], "gross_money": record["gross_money"],
            "gross_goods": record["gross_goods"]}


def largest(value):
    """The largest absolute number in a nested structure."""
    if isinstance(value, Mapping):
        return max([largest(each) for each in value.values()] + [0.0])
    if isinstance(value, (list, tuple)):
        return max([largest(each) for each in value] + [0.0])
    return abs(value) if isinstance(value, (int, float)) and abs(value) != float("inf") else 0.0


def agree(left, right, scale=None, path=""):
    """None when the two nested structures of numbers agree within TOLERANCE of the largest number in `left`, else where."""
    if scale is None:
        scale = max(1.0, largest(left))
    if isinstance(left, Mapping) or isinstance(right, Mapping):
        for key in sorted(set(left) | set(right), key=str):
            found = agree(left.get(key, 0.0), right.get(key, 0.0), scale, "%s/%s" % (path, key))
            if found:
                return found
        return None
    if isinstance(left, (list, tuple)):
        if len(left) != len(right):
            return path + " length"
        for index, (one, other) in enumerate(zip(left, right)):
            found = agree(one, other, scale, "%s/%d" % (path, index))
            if found:
                return found
        return None
    if left is None or right is None or isinstance(left, str):
        return None if left == right else path
    return None if left == right or abs(left - right) <= TOLERANCE * scale else "%s %r %r" % (path, left, right)


def traded_rounds(results):
    """The market's results up to the last that traded: a round at the end that traded nothing (a bid at dust) is no figure."""
    results = list(results)
    while len(results) > 1 and results[-1].quantity == 0.0:
        results.pop()
    return results


def market_figures(markets):
    return {key: {"delivered": market.delivered, "wanted": market.wanted, "unsold": market.unsold,
                  "offers": [(offer.seller, offer.tile, offer.quantity) for offer in market.offers],
                  "bids": [(bid.buyer, bid.budget, bid.flexible_quantity, bid.reference_price, bid.maximum_price)
                           for bid in market.all_bids],
                  "results": [(result.quantity, result.price or 0.0, result.demand_at_price, result.offered_at_price)
                              for result in traded_rounds(market.results)]}
            for key, market in markets.items()}


def ledger_figures(ledger):
    return {name: getattr(ledger, name) for name in ("money_out", "sales_in", "received", "sold", "imports_paid",
                                                     "exports_received", "delivered_by_market")}


def on_the_tables(world):
    """The world with every market's first-round bids and offers left written into a book of orders and read from its rows."""
    setup, record, view, ledger, markets, basket_of = world
    orders = GoodsOrderBook(record.book, MarketTables())
    for market in markets.values():
        bid_first, offer_first = orders.bid_count(), orders.offer_count()
        for bid in market.bids:
            orders.add_bid(bid)
        for offer in market.offers:
            orders.add_offer(offer)
        market.rows = MarketRows(orders, range(bid_first, orders.bid_count()), range(offer_first, orders.offer_count()))
        market.bids = LazyObjects(lambda rows=market.rows: orders.bids_of(rows.bid_rows), len(market.rows.bid_rows))
        market.offers = LazyObjects(lambda rows=market.rows: orders.offers_of(rows.left_rows), len(market.rows.left_rows))
        market.all_bids, market.added_bids = None, []
    return orders


def run(seed, rounds, factor=1.0):
    """A fresh economy, its first-round budgets and offers scaled by `factor`, then respent by `rounds`."""
    world = build(seed)
    nudged(world[4], factor)
    rounds(*world)
    return world


def difference(one, other):
    """Where two worlds' book, ledger and markets differ beyond TOLERANCE, else None."""
    return (agree(snapshot(one[1].book), snapshot(other[1].book)) or agree(ledger_figures(one[3]), ledger_figures(other[3]))
            or agree(market_figures(one[4]), market_figures(other[4])))


class RespendKernelAgreesWithThePythonRounds(unittest.TestCase):

    def test_random_economies_read_from_the_order_tables(self):
        def on_tables(seed, factor=1.0):
            world = build(seed)
            nudged(world[4], factor)
            goods_respend_year.respend(*world, on_the_tables(world))
            return world

        compared = 0
        for seed in range(60):
            found = difference(run(seed, respend_reference.respend_plain), on_tables(seed))
            if found and (difference(run(seed, respend_reference.respend_plain), run(seed, respend_reference.respend_plain, 1.0 + 1e-12))
                          or difference(on_tables(seed), on_tables(seed, 1.0 + 1e-12))):
                continue      # one of the two moves when every budget and offer is nudged by one part in 10^12
            compared += 1
            self.assertIsNone(found, "seed %d" % seed)
        self.assertGreater(compared, 0.9 * 60)

    def test_random_economies(self):
        compared, skipped = 0, 0
        for seed in range(60):
            old = run(seed, respend_reference.respend_plain)
            new = run(seed, goods_respend_year.respend)
            found = difference(old, new)
            if found and (difference(old, run(seed, respend_reference.respend_plain, 1.0 + 1e-12))
                          or difference(new, run(seed, goods_respend_year.respend, 1.0 + 1e-12))):
                skipped += 1      # one of the two moves when every budget and offer is nudged by one part in 10^12
                continue
            compared += 1
            self.assertIsNone(found, "seed %d" % seed)
        self.assertGreater(compared, 0.9 * (compared + skipped), "compared %d, skipped %d" % (compared, skipped))


if __name__ == "__main__":
    unittest.main()
