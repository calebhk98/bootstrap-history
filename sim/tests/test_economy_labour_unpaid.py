"""Hours an employer cannot pay for are not delivered: the workers keep them for their own plots."""
import types
import unittest

from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory
from sim.economy.types import EDGE_MINT, LabourBid, LabourOffer, Transfer
from sim.economy.year_labour import clear_labour
from sim.economy.year_ledger import YearLedger


def cleared(employer_cash):
    book = Book()
    book.transfer(Transfer(EDGE_MINT, "farm", "coin", employer_cash, "opening"))
    record = types.SimpleNamespace(book=book, memory=MarketMemory())
    setup = types.SimpleNamespace(currency_id="coin")
    bids = [LabourBid("farm", "plough", "labour:t1", 100.0, 5.0)]
    offers = [LabourOffer("family", "plough", "labour:t1", 100.0, 1.0)]
    ledger = YearLedger()
    clear_labour(setup, record, bids, offers, ledger)
    return ledger, ledger.labour_results[0]


class UnpaidLabourTests(unittest.TestCase):
    def test_an_employer_able_to_pay_receives_all_the_hours(self):
        ledger, _result = cleared(1e9)
        self.assertAlmostEqual(ledger.hours_hired["farm"]["plough"], 100.0)
        self.assertAlmostEqual(ledger.hours_sold["family"], 100.0)

    def test_an_employer_with_half_the_cash_receives_half_the_hours(self):
        _ledger, result = cleared(1e9)
        owed = result.wage * 100.0
        ledger, _result = cleared(owed / 2.0)
        self.assertAlmostEqual(ledger.hours_hired["farm"]["plough"], 50.0, places=6)
        self.assertAlmostEqual(ledger.hours_sold["family"], 50.0, places=6)


if __name__ == "__main__":
    unittest.main()
