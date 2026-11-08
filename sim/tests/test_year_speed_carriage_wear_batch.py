"""`carriage_wear_batch.settle_all` keeps and wears every merchant's carriers as `carriage_wear.settle` did merchant by merchant: the
same moves for each merchant and the same stock in the book afterwards."""

QUICK_TOPIC = True

import random
import unittest

from sim.book import Book
from sim.economy import carriage_wear, carriage_wear_batch
from sim.economy.merchants import Merchant
from sim.economy.types import EDGE_PRODUCTION, GoodsMove

GOODS = ("ox", "cart", "grain")
TILES = ("a", "b", "c")


def seeded_book(rng, merchants):
    book = Book()
    for merchant in merchants:
        for holder in (merchant, carriage_wear.account(merchant)):
            for good in GOODS:
                for tile in TILES:
                    if rng.random() < 0.5:
                        book.move(GoodsMove(EDGE_PRODUCTION, holder, good, tile, rng.uniform(0.5, 9.0), "stock"))
    return book


def stock_of(book, agents):
    return {agent: book.goods_held(agent) for agent in agents}


class SettleAllTests(unittest.TestCase):
    def test_every_merchants_moves_and_stock_are_what_settle_made(self):
        for seed in range(30):
            rng = random.Random(seed)
            names = ["m%d" % number for number in range(rng.randrange(1, 4))]
            worn = {name: {good: rng.choice((0.0, 3.0, 12.0, 40.0)) for good in GOODS[:2] if rng.random() < 0.7} for name in names}
            alone, together = seeded_book(random.Random(seed), names), seeded_book(random.Random(seed), names)
            expected = []
            for name in names:
                expected += carriage_wear.settle(Merchant(name, "a", "owner", 1.0), alone, GOODS[:2], worn[name])
            got = carriage_wear_batch.settle_all(together, names, GOODS[:2], worn)
            holders = names + [carriage_wear.account(name) for name in names]
            self.assertEqual(stock_of(together, holders), stock_of(alone, holders), seed)
            self.assertEqual(sorted(map(repr, got)), sorted(map(repr, expected)), seed)


if __name__ == "__main__":
    unittest.main()
