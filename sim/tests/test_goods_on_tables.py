"""The goods orders as tables (docs/architecture/COMPILED_YEAR.md, stage 2): the book of orders keeps bids and offers in the order they
arrive, from objects or from rows, and gives the objects back; a good's rows are cut by market, ranked by name, and sorted into
the clearing order; the quotes of markets that did not trade are the quotes the lists give. Each test calls one function on
inputs written out."""

QUICK_TOPIC = True

import math
import unittest

import numpy

from sim.book import Book
from sim.economy import goods_market_rows, goods_table_group, goods_table_pack, goods_table_quotes, market_quote
from sim.economy.goods_order_book import GoodsOrderBook
from sim.economy.goods_order_tables import HOUSEHOLD, OTHER
from sim.economy.market_tables import MarketTables
from sim.economy.types import (EDGE_MINT, QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK, Bid, GoodsMove, Offer)


def new_book() -> GoodsOrderBook:
    return GoodsOrderBook(Book(), MarketTables())


def bid(buyer, good="wheat", area="north", tile="t1", floor=1.0, flexible=2.0, reference=3.0, elasticity=0.5, budget=40.0, priority=0,
        maximum=math.inf):
    return Bid(buyer, good, area, tile, floor, flexible, reference, elasticity, budget, priority, maximum_price=maximum)


def offer(seller, good="wheat", area="north", tile="t1", quantity=5.0, reservation=2.0):
    return Offer(seller, good, area, tile, quantity, reservation)


class OrderBookKeepsArrivalOrder(unittest.TestCase):

    def test_objects_and_rows_come_back_in_the_order_they_arrived(self):
        orders = new_book()
        first, second = bid("b2"), bid("b1", priority=1, maximum=9.0)
        orders.add_bid(first)
        orders.add_orders(type("Orders", (), {"bids": (second,), "offers": (offer("s1"),)})())
        third = bid("b0", floor=0.0)
        buyer = orders.book.agent_number("b0")
        market = orders.market_id("wheat", "north")
        orders.append_bids([buyer], [orders.book.good_number("wheat")], [orders.book.tile_number("t1")], [market], [0],
                           [[0.0, 2.0, 3.0, 0.5, 40.0, math.inf]], HOUSEHOLD)
        self.assertEqual(orders.bids_of(range(orders.bid_count())), [first, second, third])
        self.assertEqual(orders.tables()[0].sequence[:3].tolist(), [0, 1, 2])
        self.assertEqual(orders.tables()[0].source[:3].tolist(), [OTHER, OTHER, HOUSEHOLD])

    def test_the_dict_door_appends_to_the_market_named(self):
        orders = new_book()
        orders.setdefault(("wheat", "north"), ([], []))[0].append(bid("b1"))
        orders.setdefault(("wheat", "north"), ([], []))[1].append(offer("s1"))
        self.assertEqual((orders.bid_count(), orders.offer_count()), (1, 1))
        self.assertEqual(orders.offers_of([0]), [offer("s1")])

    def test_a_market_is_numbered_once_for_its_good_and_area(self):
        orders = new_book()
        self.assertEqual(orders.market_id("wheat", "north"), orders.market_id("wheat", "north"))
        self.assertNotEqual(orders.market_id("wheat", "north"), orders.market_id("wheat", "south"))

    def test_a_new_offer_has_all_its_units_left_and_no_result(self):
        orders = new_book()
        orders.add_offer(offer("s1", quantity=7.0))
        table = orders.tables()[1]
        self.assertEqual((table.quantity_left[0], table.quantity_sold[0], table.rank[0]), (7.0, 0.0, -1))


class GoodsRowsAreCutByMarket(unittest.TestCase):

    def book_of_two_markets(self):
        orders = new_book()
        for each in (bid("b1", area="south"), bid("b2", area="north"), bid("b3", area="south"), bid("w", good="rye")):
            orders.add_bid(each)
        for each in (offer("s1", area="south"), offer("s2", area="north", quantity=0.0), offer("e", area="north")):
            orders.add_offer(each)
        return orders

    def test_rows_of_good_lists_the_markets_in_area_name_order_with_arrival_order_inside(self):
        orders = self.book_of_two_markets()
        rows = goods_table_group.rows_of_good(orders, orders.book.good_number("wheat"))
        self.assertEqual([orders.area_name_of_market(market) for market in rows.markets.tolist()], ["north", "south"])
        self.assertEqual((rows.bids_of_market(0).tolist(), rows.bids_of_market(1).tolist()), ([1], [0, 2]))
        self.assertEqual((rows.offers_of_market(0).tolist(), rows.offers_of_market(1).tolist()), ([1, 2], [0]))

    def test_batch_flags_wants_units_and_no_edge_seller(self):
        orders = new_book()
        orders.add_offer(offer("s1", area="north"))
        orders.add_offer(offer("s2", area="south", quantity=0.0))
        orders.add_offer(offer("edge:mint", area="east"))
        orders.add_offer(offer("s3", area="east"))
        _bids, offers = orders.tables()
        rows = goods_table_group.rows_of_good(orders, orders.book.good_number("wheat"))
        flags = goods_table_group.batch_flags(offers, orders.book.agent_table.is_edge, rows, True)
        by_area = {orders.area_name_of_market(market): flag for market, flag in zip(rows.markets.tolist(), flags.tolist())}
        self.assertEqual(by_area, {"east": False, "north": True, "south": False})

    def test_batch_flags_are_all_false_for_a_good_the_batch_does_not_take(self):
        orders = new_book()
        orders.add_offer(offer("s1"))
        _bids, offers = orders.tables()
        rows = goods_table_group.rows_of_good(orders, orders.book.good_number("wheat"))
        self.assertEqual(goods_table_group.batch_flags(offers, orders.book.agent_table.is_edge, rows, False).tolist(), [False])

    def test_the_stock_slot_of_an_offer_is_the_book_slot_of_its_seller_good_and_tile(self):
        orders = new_book()
        orders.book.move_many([GoodsMove(EDGE_MINT, "s1", "wheat", "t1", 4.0, "start")])
        orders.add_offer(offer("s1"))
        orders.add_offer(offer("s2"))
        orders.add_offer(offer("s1", tile="t9"))
        _bids, offers = orders.tables()
        rows = goods_table_group.rows_of_good(orders, orders.book.good_number("wheat"))
        goods_table_group.note_stock_slots(offers, orders.book, orders.book.good_number("wheat"), rows.offer_rows)
        self.assertEqual(offers.stock_slot[:3].tolist(), [orders.book.slot_for("s1", "wheat", "t1"), -1, -1])
        self.assertGreaterEqual(offers.stock_slot[0], 0)

    def test_name_ranks_sort_names_as_text_whatever_their_numbers(self):
        self.assertEqual(goods_table_group.name_ranks(["b", "a", "c", "B"]).tolist(), [2, 1, 3, 0])


class ClearingOrderIsTheOldSort(unittest.TestCase):

    def test_bids_sort_by_priority_then_buyer_then_tile_with_arrival_breaking_ties(self):
        orders = new_book()
        for each in (bid("b", tile="t2"), bid("a", priority=1), bid("b", tile="t1"), bid("b", tile="t2", floor=9.0), bid("c")):
            orders.add_bid(each)
        bids, _offers = orders.tables()
        rows = goods_table_group.rows_of_good(orders, orders.book.good_number("wheat"))
        agent_rank = goods_table_group.name_ranks(orders.book.agent_ids.name_list)
        tile_rank = goods_table_group.name_ranks(orders.book.tile_ids.name_list)
        sorted_rows, slots = goods_table_pack.sorted_bids(bids, rows, numpy.array([True]), agent_rank, tile_rank)
        self.assertEqual(sorted_rows.tolist(), [2, 0, 3, 4, 1])
        self.assertEqual(slots.tolist(), [0] * 5)

    def test_offers_with_units_sort_by_seller_then_tile_and_are_numbered_by_seller_and_tile(self):
        orders = new_book()
        for each in (offer("s2"), offer("s1", tile="t2"), offer("s1", quantity=0.0), offer("s1", tile="t2", quantity=3.0), offer("s1")):
            orders.add_offer(each)
        _bids, offers = orders.tables()
        rows = goods_table_group.rows_of_good(orders, orders.book.good_number("wheat"))
        agent_rank = goods_table_group.name_ranks(orders.book.agent_ids.name_list)
        tile_rank = goods_table_group.name_ranks(orders.book.tile_ids.name_list)
        flags = numpy.array([True])
        sorted_rows, slots = goods_table_pack.sorted_offers(offers, rows, flags, agent_rank, tile_rank)
        self.assertEqual(sorted_rows.tolist(), [4, 1, 3, 0])
        pointers = numpy.array([0, 4])
        self.assertEqual(goods_table_pack.seller_tile_numbers(offers, sorted_rows, slots, pointers).tolist(), [0, 1, 1, 2])

    def test_price_scales_is_the_mean_positive_reference_else_the_last_price(self):
        pointers = numpy.array([0, 3, 4, 4])
        references = numpy.array([2.0, 0.0, 4.0, 0.0])
        scale = goods_table_pack.price_scales(pointers, references, numpy.array([9.0, 5.0, math.nan]))
        self.assertEqual(scale[:2].tolist(), [3.0, 5.0])
        self.assertTrue(math.isnan(scale[2]))


class UntradedMarketsHaveTheListsQuotes(unittest.TestCase):

    def figures(self, bids, offers, minimum=0.0, has_minimum=False):
        columns = ([each.budget for each in bids], [each.maximum_price for each in bids], [each.reservation_price for each in offers],
                   [each.quantity for each in offers])
        return goods_table_quotes.untraded_figures(
            numpy.array([0, len(bids)]), numpy.array([0, len(offers)]), *map(numpy.array, columns), numpy.array([minimum]),
            numpy.array([has_minimum]))

    def test_the_figures_give_the_quote_market_quote_gives(self):
        cases = [
            ([bid("b", maximum=1.5)], [offer("s", reservation=2.0)]),
            ([bid("b", budget=0.0, maximum=1.5)], [offer("s", reservation=2.0)]),
            ([bid("b")], [offer("s", reservation=2.0)]),
            ([], [offer("s", reservation=2.0), offer("t", reservation=-1.0), offer("u", reservation=1.0, quantity=0.0)]),
            ([bid("b", maximum=4.0)], []),
            ([bid("b", budget=0.0)], []),
            ([], []),
        ]
        for bids, offers in cases:
            lowest_ask, _clamped, _supply, funded, best_bid = self.figures(bids, offers)
            quote = goods_table_quotes.quote_of(lowest_ask[0], best_bid[0], bool(funded[0]))
            self.assertEqual(quote, market_quote.no_trade_quote(bids, offers), (bids, offers))

    def test_the_lowest_clamped_ask_and_the_supply_are_those_of_the_offers_with_units(self):
        offers = [offer("s", reservation=-1.0, quantity=2.0), offer("t", reservation=0.5, quantity=3.0), offer("u", quantity=0.0)]
        _ask, clamped, supply, _funded, _bid = self.figures([], offers, minimum=0.1, has_minimum=True)
        self.assertEqual((clamped[0], supply[0]), (0.1, 5.0))

    def test_the_price_held_is_the_last_price_unless_the_lowest_ask_is_above_it(self):
        self.assertEqual(goods_table_quotes.held_price(4.0, 3.0), 4.0)
        self.assertEqual(goods_table_quotes.held_price(4.0, 6.0), 6.0)
        self.assertEqual(goods_table_quotes.held_price(None, 6.0), 6.0)
        self.assertEqual(goods_table_quotes.held_price(None, math.nan), None)

    def test_the_wanted_quantity_is_what_the_bids_take_at_the_price_the_quote_names(self):
        bids = [bid("a"), bid("b", budget=0.0), bid("c", maximum=1.0), bid("d", flexible=0.0, floor=4.0, budget=6.0)]
        columns = [numpy.array([getattr(each, name) for each in bids]) for name in (
            "floor_quantity", "flexible_quantity", "reference_price", "elasticity", "budget", "maximum_price")]
        wanted = goods_table_quotes.wanted_by_market(numpy.array([0, 4]), numpy.array([2.0]), *columns)
        from sim.economy.goods_market import quantity_at
        self.assertAlmostEqual(wanted[0], math.fsum(quantity_at(each, 2.0) for each in bids), places=12)

    def test_the_bids_only_quote_from_rows_is_no_trade_quote_with_no_offers(self):
        orders = new_book()
        bids = [bid("a", maximum=3.0), bid("b", maximum=5.0), bid("c", budget=0.0, maximum=9.0)]
        for each in bids:
            orders.add_bid(each)
        lists = orders.bid_lists()
        for cost in (None, 2.0):
            self.assertEqual(goods_market_rows.bids_only_quote(lists, [0, 1, 2], cost), market_quote.no_trade_quote(bids, [], cost))
        self.assertEqual(goods_market_rows.bids_only_quote(lists, [2], None), None)

    def test_wanted_at_rows_is_wanted_at_over_the_rows_and_the_extra_bids(self):
        from sim.economy.market_memory_asks import wanted_at
        orders = new_book()
        rows = [bid("a"), bid("b", maximum=1.0), bid("edge:external:foreign", floor=50.0)]
        extra = [bid("d", budget=6.0)]
        for each in rows:
            orders.add_bid(each)
        self.assertEqual(goods_market_rows.wanted_at_rows(orders.bid_lists(), [0, 1, 2], 2.0, extra), wanted_at(rows + extra, 2.0))
        self.assertEqual(goods_market_rows.wanted_at_rows(orders.bid_lists(), [0], 0.0), 0.0)


class CohortBidRowsAreTheCohortsBids(unittest.TestCase):

    def rows_for(self, budgets, plan=0.0, store_budgets=()):
        """The kernel's answer for one cohort whose template has one priced good per budget (all switched on) and a store good per
        store budget."""
        from sim.economy.households_bid_rows import cohort_bid_rows
        from sim.economy.households_orders_kernel import RO_COUNT, SO_COUNT
        count, stores = len(budgets), len(store_budgets)
        rows = numpy.zeros((count, RO_COUNT))
        rows[:, 0], rows[:, 1], rows[:, 2], rows[:, 3], rows[:, 4] = 1.0, 2.0, 3.0, budgets, math.inf
        store_rows = numpy.zeros((stores, SO_COUNT))
        store_rows[:, 0], store_rows[:, 1] = store_budgets, 5.0
        return cohort_bid_rows(
            numpy.array([7]), numpy.array([9]), numpy.array([0]), numpy.array([0]), numpy.array([0]), numpy.array([plan]),
            numpy.array([0, count]), numpy.arange(count), numpy.array([0]), numpy.array([0]), numpy.array([stores]), numpy.array([1.5]),
            numpy.arange(count) + 100, numpy.arange(count) + 200, numpy.ones(count, dtype=numpy.int64), numpy.full(count, 4.0),
            numpy.arange(stores) + 300, numpy.arange(stores) + 400, numpy.full(stores, 6.0), rows, store_rows)

    def test_the_priced_goods_come_first_in_name_order_then_the_store_goods_with_a_budget(self):
        buyer, good, tile, market, priority, figures, planned = self.rows_for([10.0, 20.0], plan=1.0, store_budgets=[0.0, 5.0])
        self.assertEqual((buyer.tolist(), good.tolist(), tile.tolist(), market.tolist()), ([7, 7, 7], [100, 101, 301], [9, 9, 9], [200, 201, 401]))
        self.assertEqual(priority.tolist(), [1, 1, 2])
        self.assertEqual(figures[2].tolist(), [0.0, 5.0, 6.0, 1.5, 5.0, math.inf])
        self.assertEqual(planned.tolist(), [35.0])

    def test_a_cohort_without_a_store_plan_bids_for_no_store_good(self):
        self.assertEqual(len(self.rows_for([10.0], plan=0.0, store_budgets=[5.0])[0]), 1)

    def test_planned_spending_is_the_sum_python_takes_of_the_budgets(self):
        budgets = [1e16, 1.0, -1e16, 1.0]       # added left to right these give 1.0; Python's sum of floats keeps the low digits
        self.assertEqual(self.rows_for(budgets)[6].tolist(), [sum(budgets)])
        self.assertNotEqual(sum(budgets), ((budgets[0] + budgets[1]) + budgets[2]) + budgets[3])


class QuoteKinds(unittest.TestCase):

    def test_the_quote_kinds_are_the_ones_the_lists_name(self):
        self.assertEqual(goods_table_quotes.quote_of(2.0, 1.0, True).kind, QUOTE_BEST_UNFILLED_BID)
        self.assertEqual(goods_table_quotes.quote_of(2.0, math.nan, False).kind, QUOTE_LOWEST_UNFILLED_ASK)


if __name__ == "__main__":
    unittest.main()
