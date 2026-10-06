"""Hours an employer cannot pay for are not delivered: the workers keep them for their own plots."""
import types
import unittest

from sim.economy.accounts import Book
from sim.labour.api import MarketState, YearInputs as CoreInputs
from sim.labour.market.aptitude import split_evenly
from sim.economy.market_memory import MarketMemory
from sim.economy.types import EDGE_MINT, LabourBid, LabourOffer, Transfer
from sim.economy.year_labour import clear_labour
from sim.economy.year_ledger import YearLedger


def cleared(employer_cash):
    book = Book()
    book.transfer(Transfer(EDGE_MINT, "farm", "coin", employer_cash, "opening"))
    state = MarketState(workers={"labour:t1": {"plough": split_evenly(0.05)}},
                        hired_hours={"labour:t1": {"plough": {"farm": 100.0}}})   # the farm's hands stay on
    record = types.SimpleNamespace(book=book, memory=MarketMemory(), workforce=state)
    setup = types.SimpleNamespace(currency_id="coin", trades={}, unskilled_trade="plough")
    bids = [LabourBid("farm", "plough", "labour:t1", 100.0, 5.0)]
    offers = [LabourOffer("family", "plough", "labour:t1", 100.0, 1.0)]
    ledger = YearLedger()
    context = CoreInputs(trades={}, bids=(), subsistence_per_worker_year={"labour:t1": 2000.0},
                         hours_per_worker_year=2000.0, discount_rate=0.05, career_years=30.0)
    clear_labour(setup, record, bids, offers, ledger, context)
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
