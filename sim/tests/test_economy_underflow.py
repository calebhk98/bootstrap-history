"""A balance left a float's underflow below zero (smaller than the smallest normal float) is rounding
residue, not an overdraft; a real overdraft still fails."""
import unittest

from sim.economy.accounts import Book, InsufficientFunds
from sim.economy.types import Transfer


class UnderflowTests(unittest.TestCase):
    def test_a_subnormal_residue_is_not_an_overdraft(self):
        book = Book()
        book.transfer(Transfer("edge:issue", "a", "coin", 1e-320, "seed"))
        book.post([Transfer("a", "b", "coin", 1e-320 + 5e-324, "pay")], [])   # leaves -5e-324

    def test_a_real_overdraft_still_fails(self):
        book = Book()
        book.transfer(Transfer("edge:issue", "a", "coin", 1.0, "seed"))
        with self.assertRaises(InsufficientFunds):
            book.transfer(Transfer("a", "b", "coin", 1.5, "pay"))


if __name__ == "__main__":
    unittest.main()
