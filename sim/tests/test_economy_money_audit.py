"""The money audit reads the supply without the edge accounts: a leak through an unnamed edge shows
up in it although the book's own conservation check stays at zero."""

QUICK_TOPIC = True

import unittest

from sim.economy import money_audit
from sim.economy.accounts import Book
from sim.economy.merchants import EDGE_CARRIAGE
from sim.economy.types import EDGE_LEGACY, EDGE_MINT, EDGE_PRODUCTION, CurrencySpec, GoodsMove, Transfer


class Holder:
    def __init__(self, book, currency):
        self.book, self.currency = book, currency


def holder(regime="fiat", backing=None, per_unit=0.0):
    book = Book()
    book.transfer(Transfer(EDGE_MINT, "alice", "coin", 100.0, "opening"))
    book.start_year()
    return Holder(book, CurrencySpec("coin", regime, backing, per_unit, None))


class AuditTests(unittest.TestCase):
    def test_a_closed_year_has_no_residual_and_nothing_unexpected(self):
        record = holder()
        record.book.transfer(Transfer("alice", "bob", "coin", 30.0, "rent"))
        report = money_audit.year_report(record)
        self.assertTrue(report.ok)
        self.assertEqual(report.supply_change["coin"], 0.0)

    def test_a_leak_through_the_legacy_edge_is_flagged_while_conservation_stays_zero(self):
        record = holder()
        record.book.transfer(Transfer(EDGE_LEGACY, "bob", "coin", 40.0, "unnamed"))
        self.assertEqual(record.book.check_conservation(1e-9).money["coin"], 0.0)
        report = money_audit.year_report(record)
        self.assertFalse(report.ok)
        self.assertEqual(report.unexpected[0][:3], (EDGE_LEGACY, "coin", 40.0))
        self.assertEqual(report.supply_change["coin"], 40.0)
        self.assertAlmostEqual(report.residual["coin"], 0.0)

    def test_carriage_edge_money_is_flagged(self):
        record = holder()
        record.book.transfer(Transfer("alice", EDGE_CARRIAGE, "coin", 5.0, "carriage"))
        self.assertEqual(money_audit.year_report(record).unexpected[0][0], EDGE_CARRIAGE)

    def test_mint_metal_gap_against_the_backing(self):
        record = holder("struck_coin", "silver", 0.5)
        record.book.move(GoodsMove(EDGE_PRODUCTION, EDGE_MINT, "silver", "t1", 60.0, "ore"))
        self.assertAlmostEqual(money_audit.year_report(record).metal_gap["coin"], 60.0 - 100.0 * 0.5)


if __name__ == "__main__":
    unittest.main()
