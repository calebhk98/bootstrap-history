"""The audit's metal gap is read at a consistent point: coin wear booked at year close, after the mint
last matched its metal to the coin, is not a gap; it is reported as metal awaiting wear."""
import unittest

from sim.economy import money_audit
from sim.economy.accounts import Book
from sim.economy.metal_stock import yearly_wear
from sim.economy.types import EDGE_MINT, EDGE_PRODUCTION, CurrencySpec, GoodsMove, Transfer


class Holder:
    def __init__(self, book, currency):
        self.book, self.currency = book, currency


def worn_book(metal):
    book = Book()
    book.transfer(Transfer(EDGE_MINT, "alice", "coin", 1000.0, "opening"))
    book.move(GoodsMove(EDGE_PRODUCTION, EDGE_MINT, "silver", "t1", metal, "metal"))
    book.start_year()
    spec = CurrencySpec("coin", "struck_coin", "silver", 0.005, None)
    book.transfer_many(yearly_wear({"alice": 1000.0}, spec))
    return Holder(book, spec)


class SyntheticWear(unittest.TestCase):
    def test_wear_after_reconciliation_is_not_a_gap(self):
        audit = money_audit.year_report(worn_book(5.0))
        self.assertAlmostEqual(audit.metal_gap["coin"], 0.0, places=9)
        self.assertAlmostEqual(audit.metal_awaiting_wear["coin"], 10.0 * 0.005, places=9)

    def test_a_real_excess_still_shows(self):
        self.assertAlmostEqual(money_audit.year_report(worn_book(6.0)).metal_gap["coin"], 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
