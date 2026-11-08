"""The kept price response gives what `market_curves.price_response` gives, and is served again only for the book object it was
worked out from."""

QUICK_TOPIC = True

import math
import unittest
from unittest import mock

from sim.economy import market_curves, response_memo

BOOK = {"bids": [[0.0, 10.0, 2.0, 1.0, 40.0, None], [5.0, 0.0, 0.0, 0.0, 30.0, 4.0]], "offers": [[1.0, 6.0], [2.5, 9.0]]}
ASKS = [(None, 0.0, 0.0), (2.0, 3.0, 0.0), (2.0, 0.0, 3.0), (None, 0.0, 4.5), (1.5, 100.0, 0.0), (1.5, 0.0, 1000.0)]


def same(left, right):
    return left is right or (left is not None and right is not None and (left == right or (math.isnan(left) and math.isnan(right))))


class ResponseMemoTests(unittest.TestCase):
    def setUp(self):
        response_memo._RESPONSES.clear()

    def test_the_kept_answer_is_the_clearing_s_for_every_ask(self):
        for last_price, landed, taken in ASKS:
            expected = market_curves.price_response(BOOK, "grain", last_price, landed, taken)
            self.assertTrue(same(response_memo.price_response(BOOK, "grain", last_price, landed, taken), expected), (last_price, landed, taken))
            self.assertTrue(same(response_memo.price_response(BOOK, "grain", last_price, landed, taken), expected), (last_price, landed, taken))

    def test_a_repeated_ask_of_the_same_book_clears_once(self):
        with mock.patch.object(market_curves, "price_response", wraps=market_curves.price_response) as clearing:
            first = response_memo.price_response(BOOK, "grain", 2.0, 3.0, 0.0)
            second = response_memo.price_response(BOOK, "grain", 2.0, 3.0, 0.0)
        self.assertEqual(first, second)
        self.assertEqual(clearing.call_count, 1)

    def test_a_new_book_object_with_other_content_is_cleared_afresh(self):
        other = {"bids": [list(row) for row in BOOK["bids"]], "offers": [[1.0, 1.0], [2.5, 1.0]]}
        kept = response_memo.price_response(BOOK, "grain", 2.0, 0.0, 3.0)
        again = response_memo.price_response(other, "grain", 2.0, 0.0, 3.0)
        self.assertEqual(again, market_curves.price_response(other, "grain", 2.0, 0.0, 3.0))
        self.assertNotEqual(kept, again)

    def test_a_book_that_traded_nothing_answers_none_and_that_is_kept(self):
        empty = {"bids": [], "offers": [[1.0, 5.0]]}
        self.assertIsNone(response_memo.price_response(empty, "grain", None, 10.0, 0.0))
        with mock.patch.object(market_curves, "price_response") as clearing:
            self.assertIsNone(response_memo.price_response(empty, "grain", None, 10.0, 0.0))
        clearing.assert_not_called()


if __name__ == "__main__":
    unittest.main()
