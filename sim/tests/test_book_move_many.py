"""`Book.move_many` writes the stocks and records in one pass; it must leave the book as `Book.post((), moves)` does, and
refuse a batch that overdraws with nothing applied. Plain books, no game."""

QUICK_TOPIC = True

import copy
import random
import unittest

from sim.book import Book, GoodsMove, InsufficientGoods
from sim.economy.types import EDGE_CONSUMPTION, EDGE_PRODUCTION


def holdings_record(book: Book) -> dict:
    """The book's record without its numbering (a refused batch may leave a name numbered, but holds nothing of it)."""
    record = book.to_record()
    del record["numbering"]
    return record


def stocked_book(rng: random.Random) -> Book:
    book = Book()
    for agent in ("a", "b", "c"):
        for good in ("grain", "iron"):
            book.move(GoodsMove(EDGE_PRODUCTION, agent, good, "t1", rng.uniform(5.0, 50.0), "seed"))
    return book


def random_moves(rng: random.Random):
    moves = []
    for _ in range(rng.randint(0, 12)):
        giver, receiver = rng.sample(["a", "b", "c", EDGE_CONSUMPTION, EDGE_PRODUCTION], 2)
        moves.append(GoodsMove(giver, receiver, rng.choice(["grain", "iron"]), "t1", rng.uniform(0.0, 3.0),
                               rng.choice(["input", "output"])))
    return moves


class MoveManyIsPost(unittest.TestCase):
    def test_random_batches_leave_the_same_book(self):
        rng = random.Random(7)
        for _ in range(40):
            first = stocked_book(rng)
            second = copy.deepcopy(first)
            moves = random_moves(rng)
            first.move_many(moves)
            second.post((), moves)
            self.assertEqual(first.to_record(), second.to_record())

    def test_an_overdraft_applies_nothing(self):
        book = stocked_book(random.Random(1))
        before = holdings_record(book)
        with self.assertRaises(InsufficientGoods):
            book.move_many([GoodsMove("a", "b", "grain", "t1", 1e6, "input")])
        self.assertEqual(holdings_record(book), before)


if __name__ == "__main__":
    unittest.main()
