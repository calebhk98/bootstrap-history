"""economy.api.bank_dividends_to: the dividend a seat's banks paid it, read from the record."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy import api


def economy(banks, cohorts=()):
    record = types.SimpleNamespace(cohorts=set(cohorts), capital_markets=types.SimpleNamespace(banks=banks))
    return types.SimpleNamespace(record=record)


def bank(founder, paid):
    return types.SimpleNamespace(founder=founder, dividend_paid=paid)


class BankDividendsTo(unittest.TestCase):
    def test_a_seat_is_paid_the_dividends_of_the_banks_it_founded(self):
        banks = {"b1": bank("seat", 3.0), "b2": bank("seat", 4.0), "b3": bank("other", 9.0)}
        self.assertEqual(api.bank_dividends_to(economy(banks), "seat"), 7.0)

    def test_a_household_owner_is_paid_nothing_here(self):
        self.assertEqual(api.bank_dividends_to(economy({"b1": bank("tile", 3.0)}, cohorts={"tile"}), "tile"), 0.0)


if __name__ == "__main__":
    unittest.main()
