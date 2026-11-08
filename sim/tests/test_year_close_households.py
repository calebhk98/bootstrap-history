"""The households' year-end goods as tables (year_close_household_kernels.py, year_close_households.py) against the per-cohort Python they
replace: the receipts and grown goods merged, and the consumption moves cut to what is held, booked one batch for each cohort."""
QUICK_TOPIC = True

import unittest

import numpy as np

from sim.book import Book, GoodsMove
from sim.economy import households_close
from sim.economy.types import EDGE_CONSUMPTION, GoodSpec
from sim.economy.year_close import held_only
from sim.economy.year_close_household_kernels import consumption_postings, receipts_with_grown
from sim.economy.year_close_households import _durable_flags, _good_ranks, _number_unseen, _post_consumption
from sim.economy.year_ledger import YearLedger

SPECS = {"wheat": GoodSpec("wheat", 1.0, 0.0, 0.0, "food"), "tool": GoodSpec("tool", 1.0, 0.0, 5.0, "tool"),
         "barley": GoodSpec("barley", 1.0, 0.0, 0.0, "food")}
RECEIVED = {"c2": {"wheat": 3.0, "tool": 1.0, "barley": 2.5}, "c1": {"wheat": 1e16, "salt": 4.0}, "c3": {}}
GROWN = {"c1": {"wheat": 1.0, "oats": 2.0}, "c3": {"barley": 7.0}, "c4": {"wheat": 0.5}}
TILES = {"c1": "t1", "c2": "t2", "c3": "t1", "c4": "t3", "c5": "t1"}


def ledger_of():
    ledger = YearLedger()
    for agent, goods in RECEIVED.items():
        ledger.received.setdefault(agent, {}).update(goods)
    for agent, goods in GROWN.items():
        ledger.grown.setdefault(agent, {}).update(goods)
    return ledger


def old_receipts(ledger, agent):
    """The dictionary the old household loop made."""
    received = dict(ledger.received.get(agent, {}))
    for good, quantity in ledger.grown.get(agent, {}).items():
        received[good] = received.get(good, 0.0) + quantity
    return received


def tables_of(ledger, agents):
    tables = ledger.tables
    numbers = np.array([tables.book.agent_ids.numbers.get(each, -1) for each in agents], dtype=np.int64)
    figures = tables.figures
    start, goods, amounts = receipts_with_grown(figures.first_received, tables.pairs["received"].rows.table, figures.first_grown,
                                                tables.pairs["grown"].rows.table, numbers)
    return numbers, start, goods, amounts


class ReceiptsTests(unittest.TestCase):
    def test_received_and_grown_goods_merge_as_the_dictionary_did_and_an_unknown_agent_has_nothing(self):
        ledger = ledger_of()
        agents = ["c1", "c2", "c3", "c4", "c5"]
        _numbers, start, goods, amounts = tables_of(ledger, agents)
        names = ledger.tables.book.good_ids.name_list
        for position, agent in enumerate(agents):
            first, last = start[position], start[position + 1]
            merged = dict(zip([names[each] for each in goods[first:last].tolist()], amounts[first:last].tolist()))
            self.assertEqual(list(merged.items()), list(old_receipts(ledger, agent).items()))


def held_book():
    book = Book()
    for agent, tile, good, quantity in (("c1", "t1", "wheat", 5.0), ("c1", "t1", "salt", 9.0), ("c2", "t2", "barley", 1.0),
                                        ("c2", "t2", "tool", 1.0), ("c3", "t1", "barley", 100.0), ("c4", "t3", "wheat", 0.0)):
        book.move(GoodsMove("edge:production", agent, good, tile, quantity, "seed"))
    return book


class ConsumptionTests(unittest.TestCase):
    def rows(self, book, ledger, agents):
        _numbers, start, goods, amounts = tables_of(ledger, agents)
        names = ledger.tables.book.good_ids.name_list
        book_goods = {name: book.good_number(name) for name in names}
        # the kernel reads goods by the book's numbering: the ledger here has its own, so translate the entries
        translated = np.array([book_goods[names[each]] for each in goods.tolist()], dtype=np.int64)
        book_agents = np.array([book.agent_ids.numbers.get(each, -1) for each in agents], dtype=np.int64)
        tiles = np.array([book.tile_ids.numbers.get(TILES[each], -1) for each in agents], dtype=np.int64)
        return consumption_postings(start, translated, amounts, book_agents, tiles, _durable_flags(book, SPECS),
                                    _good_ranks(book.good_ids.name_list), book.stock_rows.table, book.stock_rows.index)

    def test_the_rows_are_the_old_moves_cut_to_the_stock_held_in_good_name_order(self):
        book, ledger, agents = held_book(), ledger_of(), ["c1", "c2", "c3", "c4", "c5"]
        givers, goods, tiles, quantities, batches, owners = self.rows(book, ledger, agents)
        _number_unseen(book, (givers, goods, tiles, quantities, batches, owners), agents, [TILES[each] for each in agents])
        old = []
        for batch, agent in enumerate(agents):
            moves = households_close.consumption_moves(
                type("Cohort", (), {"agent_id": agent, "tile": TILES[agent]})(), old_receipts(ledger, agent), SPECS)
            old.extend((move.giver, move.good, move.tile, move.quantity) for move in held_only(moves, book))
        names = book.agent_ids.name_list
        new = [(names[giver], book.good_ids.name_list[good], book.tile_ids.name_list[tile], quantity)
               for giver, good, tile, quantity in zip(givers.tolist(), goods.tolist(), tiles.tolist(), quantities.tolist())]
        self.assertEqual(new, old)
        self.assertEqual(batches.tolist(), sorted(batches.tolist()))

    def test_booked_one_batch_for_each_cohort_the_book_ends_as_move_many_for_each_cohort_leaves_it(self):
        agents = ["c1", "c2", "c3", "c4", "c5"]
        by_rows, by_moves, ledger = held_book(), held_book(), ledger_of()
        rows = self.rows(by_rows, ledger, agents)
        _number_unseen(by_rows, rows, agents, [TILES[each] for each in agents])
        _post_consumption(by_rows, rows)
        for agent in agents:
            moves = households_close.consumption_moves(
                type("Cohort", (), {"agent_id": agent, "tile": TILES[agent]})(), old_receipts(ledger, agent), SPECS)
            by_moves.move_many(held_only(moves, by_moves))
        for agent in by_moves.agents() + [EDGE_CONSUMPTION]:
            self.assertEqual(by_rows.goods_of(agent), by_moves.goods_of(agent))
        self.assertEqual(by_rows.numbering_state(), by_moves.numbering_state())
        self.assertEqual(by_rows.gross_goods(), by_moves.gross_goods())
        self.assertEqual(by_rows.goods_flow("wheat"), by_moves.goods_flow("wheat"))


if __name__ == "__main__":
    unittest.main()
