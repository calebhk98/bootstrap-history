"""`goods_production`: the block reads and the batch posting of a producers' turn against the per-item calls they replace.
`read_stocks` against `Book.stock`, `post_lines` against `Book.move_many` of the same moves (the book afterwards, and the refusal of
a batch that would overdraw), `note_output` against `YearLedger.note_output`, and `producers.production_lines` against the moves
`producers.produce` returns (under numba and ROME_NO_JIT=1)."""
QUICK_TOPIC = True

import random
import unittest

from sim.book import Book, InsufficientGoods
from sim.economy import goods_production, producers
from sim.economy.types import EDGE_CONSUMPTION, EDGE_MINT, EDGE_PRODUCTION, GoodsMove
from sim.economy.year_ledger import YearLedger

AGENTS, GOODS, TILES = ("p1", "p2", "p3"), ("grain", "flour", "salt"), ("t1", "t2")


def funded_book(seed, full=False):
    rng = random.Random(seed)
    book = Book()
    for agent in AGENTS:
        for good in GOODS:
            for tile in TILES:
                if full or rng.random() < 0.6:
                    book.post([], [GoodsMove(EDGE_MINT, agent, good, tile, rng.uniform(20.0, 30.0), "start")])
    return book


def book_state(book):
    return [[[book.stock(agent, good, tile) for tile in TILES] for good in GOODS] for agent in AGENTS + (EDGE_CONSUMPTION, EDGE_PRODUCTION)]


class ReadStocksIsBookStock(unittest.TestCase):

    def test_random_cells_read_as_book_stock_reads_them(self):
        for seed in range(30):
            book = funded_book(seed)
            rng = random.Random(seed)
            cells = [(rng.choice(AGENTS + ("nobody",)), rng.choice(GOODS + ("unheld",)), rng.choice(TILES + ("nowhere",))) for _ in range(40)]
            self.assertEqual(goods_production.read_stocks(book, cells), [book.stock(*cell) for cell in cells], seed)

    def test_no_cells_read_as_an_empty_list(self):
        self.assertEqual(goods_production.read_stocks(Book(), []), [])


class PostLinesIsMoveMany(unittest.TestCase):

    def lines(self, rng, count):
        lines = []
        for _ in range(count):
            agent, good, tile = rng.choice(AGENTS), rng.choice(GOODS), rng.choice(TILES)
            lines.append((agent, EDGE_CONSUMPTION, good, tile, rng.uniform(0.0, 1.0), "input"))
            lines.append((EDGE_PRODUCTION, agent, rng.choice(GOODS), tile, rng.uniform(0.0, 5.0), "output"))
        return lines

    def test_random_batches_leave_the_book_as_move_many_leaves_it(self):
        for seed in range(30):
            rng = random.Random(seed)
            lines = self.lines(rng, 8)
            fast, plain = funded_book(seed, True), funded_book(seed, True)
            goods_production.post_lines(fast, lines)
            plain.move_many([GoodsMove(*line) for line in lines])
            self.assertEqual(book_state(fast), book_state(plain), seed)

    def test_a_name_the_book_has_not_met_is_numbered_by_the_old_path(self):
        fast, plain = funded_book(1), funded_book(1)
        lines = [(EDGE_PRODUCTION, "p1", "fresh_good", "t1", 2.0, "output")]
        goods_production.post_lines(fast, lines)
        plain.move_many([GoodsMove(*line) for line in lines])
        self.assertEqual((fast.stock("p1", "fresh_good", "t1"), fast.good_ids.name_list), (2.0, plain.good_ids.name_list))

    def test_a_batch_that_overdraws_a_stock_is_refused_whole_with_the_books_error(self):
        book = funded_book(2)
        before = book_state(book)
        lines = [(EDGE_PRODUCTION, "p1", "grain", "t1", 1.0, "output"), ("p2", EDGE_CONSUMPTION, "salt", "t2", 1.0e9, "input")]
        with self.assertRaises(InsufficientGoods):
            goods_production.post_lines(book, lines)
        self.assertEqual(book_state(book), before)


class NoteOutputIsLedgerNoteOutput(unittest.TestCase):

    def test_the_goods_a_producer_receives_are_added_to_its_output_in_order(self):
        lines = [("p1", EDGE_CONSUMPTION, "grain", "t1", 3.0, "input"), (EDGE_PRODUCTION, "p1", "flour", "t1", 2.5, "output"),
                 ("p2", EDGE_CONSUMPTION, "salt", "t1", 1.0, "input"), (EDGE_PRODUCTION, "p2", "flour", "t1", 4.0, "output"),
                 (EDGE_PRODUCTION, "p1", "flour", "t1", 0.5, "output")]
        book = funded_book(0)
        fast, plain = YearLedger(book=book), YearLedger(book=book)
        goods_production.note_output(fast, book, lines)
        for agent in ("p1", "p2"):
            plain.note_output(agent, [GoodsMove(*line) for line in lines if line[0] == agent or line[1] == agent])
        self.assertEqual(sorted(fast.output.items()), sorted(plain.output.items()))


class ProductionLinesAreTheMoves(unittest.TestCase):

    def test_produce_returns_the_goods_moves_of_the_lines(self):
        from sim.tests.year_close_fixture import economy_of       # a random economy: producers with recipes that have inputs and outputs
        setup, record = economy_of(1)[:2]
        producer = next(each for each in record.producers.values() if setup.recipes[each.recipe_id].inputs)
        recipe = setup.recipes[producer.recipe_id]
        held = {good: 100.0 for good in recipe.inputs}
        hours = {trade: 1.0e6 for trade in recipe.labour_hours}
        achieved, lines = producers.production_lines(producer, recipe, held, hours, producer.capacity_runs)
        achieved_again, moves = producers.produce(producer, recipe, held, hours, producer.capacity_runs)
        self.assertEqual((achieved, [GoodsMove(*line) for line in lines]), (achieved_again, moves))


if __name__ == "__main__":
    unittest.main()
