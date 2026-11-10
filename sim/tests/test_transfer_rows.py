"""`transfer_rows.post_payments`: payments given as lists of names and amounts leave the book as `transfer_many` leaves it, with the same
numbering of agents, currencies and purposes, and a refused batch raises the book's own error and posts nothing."""

QUICK_TOPIC = True

import unittest

from sim.book import Book
from sim.book_types import InsufficientFunds
from sim.economy import transfer_rows
from sim.economy.types import EDGE_MINT, Transfer


def funded_book() -> Book:
    book = Book()
    for agent, amount in (("zeta", 100.0), ("alpha", 50.0), ("mu", 10.0)):
        book.transfer(Transfer(EDGE_MINT, agent, "coin", amount, "test coin"))
    return book


PAYMENTS = (["zeta", "alpha", "zeta"], ["beta", "gamma", "alpha"], ["coin", "coin", "gold"], [30.0, 5.0, 0.0],
            ["loan_service:loan:x:3", "loan_service:loan:a:3", "loan_service:loan:b:3"])


class PostPayments(unittest.TestCase):
    def test_the_book_ends_as_transfer_many_leaves_it(self):
        by_rows, by_objects = funded_book(), funded_book()
        transfer_rows.post_payments(by_rows, *PAYMENTS)
        by_objects.transfer_many([Transfer(*each) for each in zip(*PAYMENTS)])
        self.assertEqual(by_rows.agent_ids.names, by_objects.agent_ids.names)
        self.assertEqual(by_rows.currency_ids.names, by_objects.currency_ids.names)
        self.assertEqual(by_rows.purposes.state(), by_objects.purposes.state())
        for agent in by_objects.agent_ids.names:
            for currency in by_objects.currency_ids.names:
                self.assertEqual(by_rows.balance(agent, currency), by_objects.balance(agent, currency))

    def test_no_payments_change_nothing(self):
        book = funded_book()
        names = book.agent_ids.names
        transfer_rows.post_payments(book, [], [], [], [], [])
        self.assertEqual(book.agent_ids.names, names)

    def test_a_batch_the_payer_cannot_cover_raises_the_books_error_and_posts_nothing(self):
        book = funded_book()
        with self.assertRaises(InsufficientFunds):
            transfer_rows.post_payments(book, ["mu", "mu"], ["a", "b"], ["coin", "coin"], [6.0, 6.0], ["x", "y"])
        self.assertEqual(book.balance("mu", "coin"), 10.0)


if __name__ == "__main__":
    unittest.main()
