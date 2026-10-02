"""Economy._lend: the credit rate answers borrowers even when nobody has savings on offer."""
import types
import unittest
from unittest import mock

from sim.economy import economy as economy_module
from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory
from sim.economy.types import LoanRequest

MONEY = "coin"


def lend_without_funds(last_rate, ceiling):
    memory = MarketMemory()
    memory.rates[MONEY] = last_rate
    request = LoanRequest("borrower", MONEY, 100.0, ceiling, 4.0, 0.0, "expansion")
    record = types.SimpleNamespace(memory=memory, loans=[], loan_requests=[request], expansion_runs={"borrower": 3.0},
                                   remembered_defaults={}, merchants={}, book=Book(), producers={})
    fake = types.SimpleNamespace(record=record, setup=types.SimpleNamespace(currency_id=MONEY), area_map=None,
                                 carriage=None)
    with mock.patch.object(economy_module.lending, "household_requests", return_value=[]), \
            mock.patch.object(economy_module.lending, "merchant_requests", return_value=[]):
        plant_runs = economy_module.Economy._lend(fake, [], types.SimpleNamespace(year=0), {}, None)
    return record, plant_runs


class LendWithoutFundsTests(unittest.TestCase):
    def test_borrowers_with_no_lenders_pull_the_rate_up_toward_their_ceiling(self):
        record, _runs = lend_without_funds(0.05, 0.30)
        self.assertGreater(record.memory.rates[MONEY], 0.05)

    def test_the_years_expansion_requests_are_cleared_even_when_nothing_was_lent(self):
        record, plant_runs = lend_without_funds(0.05, 0.30)
        self.assertEqual(record.expansion_runs, {})
        self.assertEqual(plant_runs, {})


if __name__ == "__main__":
    unittest.main()
