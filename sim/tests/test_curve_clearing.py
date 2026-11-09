"""A summarised book's price response from columns (`curve_clearing`) gives, bit for bit, what the objects give (`market_curves.price_response_objects`)."""

QUICK_TOPIC = True

import math
import random
import unittest

from sim.economy import curve_clearing, market_curves

WRITTEN = [
    {"bids": [[0.0, 10.0, 2.0, 1.0, 40.0, None], [5.0, 0.0, 0.0, 0.0, 30.0, 4.0]], "offers": [[1.0, 6.0], [2.5, 9.0]]},
    {"bids": [[3.0, 8.0, 1.5, 0.5, 100.0, None]], "offers": [[0.0, 2.0], [1.0, 5.0], [3.0, 4.0]]},
    {"bids": [[0.0, 0.0, 0.0, 0.0, 10.0, None]], "offers": [[1.0, 1.0]]},
    {"bids": [[2.0, 6.0, 3.0, 2.0, 50.0, 2.5], [1.0, 3.0, 2.0, 1.0, 20.0, None], [4.0, 0.0, 0.0, 0.0, 9.0, 6.0]], "offers": [[0.5, 3.0], [2.0, 3.0]]},
    {"bids": [], "offers": [[1.0, 3.0]]},
    {"bids": [[1.0, 1.0, 1.0, 1.0, 5.0, None]], "offers": []},
]
ASKS = [(None, 0.0, 0.0), (2.0, 3.0, 0.0), (2.0, 0.0, 3.0), (None, 0.0, 4.5), (1.5, 100.0, 0.0), (1.5, 0.0, 1000.0), (0.8, 2.0, 2.0), (None, 7.0, 1.0)]


def same(left, right):
    return left is right or (left is not None and right is not None and (left == right or (math.isnan(left) and math.isnan(right))))


def random_book(draw):
    bids = []
    for _ in range(draw.randint(1, 7)):
        flexible = draw.choice([0.0, draw.uniform(0.5, 20.0)])
        reference = draw.uniform(0.5, 4.0) if flexible > 0.0 else 0.0
        bids.append([draw.choice([0.0, draw.uniform(0.1, 6.0)]), flexible, reference, draw.uniform(0.2, 2.5) if flexible > 0.0 else 0.0,
                     draw.uniform(1.0, 120.0), draw.choice([None, None, draw.uniform(1.0, 6.0)])])
    offers = sorted([draw.choice([0.0, draw.uniform(0.2, 5.0)]), draw.uniform(0.5, 15.0)] for _ in range(draw.randint(1, 6)))
    return {"bids": bids, "offers": offers}


class CurveClearingTests(unittest.TestCase):
    def check(self, book, ask):
        last_price, landed, taken = ask
        expected = market_curves.price_response_objects(book, "grain", last_price, landed, taken)
        try:
            found = curve_clearing.price_response(book, last_price, landed, taken, market_curves.goods_market.MINIMUM_PRICE_SHARE_OF_REFERENCE)
        except curve_clearing.NeedsObjects:
            return False
        self.assertTrue(same(found, expected), (book, ask, found, expected))
        return True

    def test_written_books_give_the_objects_answer_for_every_ask(self):
        answered = sum(self.check(book, ask) for book in WRITTEN for ask in ASKS)
        self.assertGreater(answered, len(WRITTEN) * len(ASKS) // 2)

    def test_random_books_give_the_objects_answer(self):
        draw = random.Random(7)
        answered = 0
        for _ in range(150):
            book = random_book(draw)
            for ask in ASKS:
                answered += self.check(book, ask)
        self.assertGreater(answered, 600)

    def test_the_public_response_is_the_columns_answer(self):
        for ask in ASKS:
            self.assertTrue(same(market_curves.price_response(WRITTEN[0], "grain", *ask), market_curves.price_response_objects(WRITTEN[0], "grain", *ask)))


if __name__ == "__main__":
    unittest.main()
