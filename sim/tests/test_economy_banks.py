"""Complaint 106: a bank is an agent. Households pledge their savings to it, it lends them on and takes the deposit
as it lends, it keeps a reserve and earns a margin, and it fails when its loans default beyond its capital: its
depositors run, and they bear the loss through the one default rule. A society without the institution founds no
bank. Each rule is called on a ledger and a record written out in the test."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import bank_service, banks, credit_claims
from sim.economy.accounts import Book
from sim.economy.types import EDGE_MINT, FundsOffer, Loan, Transfer
from sim.tests.bank_fixture import BankFixture  # noqa: F401  (test_bank_runs builds its scenarios on it)

MONEY = "coin"
INSTITUTIONS = (banks.DEPOSIT_BANKING,)
CAPITAL = 100.0
PLEDGED = 450.0         # by each of two depositors
FOUNDER, DEPOSITORS, BORROWER = "household:0", ("household:1", "household:2"), "producer:0"
BANK = "bank:0"
SETUP = types.SimpleNamespace(currency_id=MONEY)


def record_with(cash):
    """A record whose households hold `cash` {agent: money}, with no bank yet."""
    book = Book()
    for agent, amount in sorted(cash.items()):
        book.transfer(Transfer(EDGE_MINT, agent, MONEY, amount, "opening"))
    return types.SimpleNamespace(book=book, loans=[], banks={}, loss_rates={}, credit_losses={}, remembered_defaults={},
                                 cohorts={agent: types.SimpleNamespace(tile="town") for agent in cash if agent != BORROWER})


def household_cash():
    return {FOUNDER: 1000.0, DEPOSITORS[0]: 1000.0, DEPOSITORS[1]: 1000.0, BORROWER: 0.0}


def standing_bank(record):
    """The founder's bank with its capital in its purse and nothing lent."""
    bank = banks.Bank(BANK, FOUNDER, 0, paid_in=CAPITAL)
    record.banks[BANK] = bank
    record.book.transfer(Transfer(FOUNDER, BANK, MONEY, CAPITAL, "bank capital"))
    return bank


def deposit(depositor, amount, rate=0.03):
    return Loan("deposit:0:%s" % depositor, depositor, BANK, MONEY, amount, rate=rate, years_left=banks.DEPOSIT_TERM_YEARS, issued_year=0)


def bank_that_has_lent(amount=820.0):
    """(record, bank, loan): the two depositors' deposits of 450 are in the bank's purse, `amount` of it lent to a producer."""
    record = record_with(household_cash())
    bank = standing_bank(record)
    for depositor in DEPOSITORS:
        record.loans.append(deposit(depositor, PLEDGED))
        record.book.transfer(Transfer(depositor, BANK, MONEY, PLEDGED, "deposit"))
    loan = Loan("loan:0:0", BANK, BORROWER, MONEY, amount, rate=0.05, years_left=5.0, issued_year=0)
    record.book.transfer(Transfer(BANK, BORROWER, MONEY, amount, "loan"))
    record.loans.append(loan)
    return record, bank, loan


def pledges(amount=PLEDGED):
    return [FundsOffer(depositor, MONEY, amount, 0.03) for depositor in DEPOSITORS]


def new_loan(amount):
    return Loan("loan:0:0", BANK, BORROWER, MONEY, amount, rate=0.05, years_left=5.0, issued_year=0)


def balance(record, agent):
    return record.book.balance(agent, MONEY)


class DepositsAndLending(unittest.TestCase):
    def test_the_bank_offers_its_free_cash_and_what_its_depositors_pledge_less_the_reserve_it_must_keep(self):
        record = record_with(household_cash())
        bank = standing_bank(record)
        remaining, pledged = banks.intermediate(SETUP, record, pledges(), 0, INSTITUTIONS)
        self.assertEqual([offer.lender for offer in remaining], [BANK])
        self.assertAlmostEqual(remaining[0].amount, CAPITAL + (1.0 - bank.reserve_share) * 2 * PLEDGED)
        self.assertEqual(sorted(offer.lender for offer in pledged[BANK]), sorted(DEPOSITORS))

    def test_a_bank_with_capital_and_no_losses_asks_what_it_pays_depositors(self):
        record = record_with(household_cash())
        standing_bank(record)
        remaining, _pledged = banks.intermediate(SETUP, record, pledges(), 0, INSTITUTIONS)
        self.assertAlmostEqual(remaining[0].minimum_rate, 0.03)

    def test_with_nothing_lent_a_bank_with_capital_has_no_spread(self):
        record = record_with(household_cash())
        bank = standing_bank(record)
        self.assertAlmostEqual(banks.spread_of(record, bank, MONEY), 0.0)

    def test_a_deposit_exists_only_for_a_loan_the_bank_made_and_keeps_the_reserve(self):
        record = record_with(household_cash())
        bank = standing_bank(record)
        supply = record.book.money_supply(MONEY)
        self.assertEqual(banks.owed_to_depositors(record, BANK), 0.0)
        banks.draw_deposits(record, [new_loan(820.0)], {BANK: pledges()}, 0, MONEY)
        deposits = banks.owed_to_depositors(record, BANK)
        self.assertAlmostEqual(deposits, 900.0)      # 100 of its own, the other 720 from deposits that leave a fifth as reserve
        self.assertAlmostEqual(balance(record, BANK) - 820.0, bank.reserve_share * deposits)    # once the loan is paid out
        self.assertAlmostEqual(record.book.money_supply(MONEY), supply)

    def test_a_smaller_loan_takes_a_smaller_deposit(self):
        record = record_with(household_cash())
        bank = standing_bank(record)
        banks.draw_deposits(record, [new_loan(300.0)], {BANK: pledges()}, 0, MONEY)
        self.assertAlmostEqual(banks.owed_to_depositors(record, BANK), (300.0 - CAPITAL) / (1.0 - bank.reserve_share))

    def test_a_loan_the_banks_own_cash_covers_takes_no_deposit(self):
        record = record_with(household_cash())
        standing_bank(record)
        banks.draw_deposits(record, [new_loan(50.0)], {BANK: pledges()}, 0, MONEY)
        self.assertEqual(banks.owed_to_depositors(record, BANK), 0.0)

    def test_a_deposit_is_the_depositors_claim_and_the_banks_debt(self):
        record, _bank, _loan = bank_that_has_lent()
        claims = credit_claims.claims_by_lender(record.loans, MONEY)
        debts = credit_claims.debts_by_borrower(record.loans, MONEY)
        for depositor in DEPOSITORS:
            self.assertAlmostEqual(claims[depositor], 450.0)
        self.assertAlmostEqual(debts[BANK], 900.0)

    def test_a_society_without_the_institution_founds_no_bank(self):
        record = record_with(household_cash())
        offers = pledges()
        remaining, pledged = banks.intermediate(SETUP, record, offers, 0, ())
        self.assertEqual(record.banks, {})
        self.assertEqual(remaining, offers)
        self.assertEqual(pledged, {})

    def test_a_society_with_it_has_the_richest_household_found_one(self):
        cash = household_cash()
        cash[DEPOSITORS[1]] = 5000.0
        record = record_with(cash)
        banks.intermediate(SETUP, record, pledges(), 0, INSTITUTIONS)
        self.assertEqual([bank.founder for bank in record.banks.values()], [DEPOSITORS[1]])
        self.assertAlmostEqual(balance(record, next(iter(record.banks))), banks.BANK_FOUNDING_SHARE_OF_CASH * 5000.0)

    def test_the_bank_pays_its_depositors_their_rate_out_of_what_it_holds(self):
        record, _bank, _loan = bank_that_has_lent()
        before = {depositor: balance(record, depositor) for depositor in DEPOSITORS}
        received = bank_service.service_deposits(record, MONEY, 1)
        for depositor in DEPOSITORS:
            self.assertAlmostEqual(received[depositor], 450.0 * 0.03)
            self.assertAlmostEqual(balance(record, depositor) - before[depositor], 450.0 * 0.03 + 450.0 / banks.DEPOSIT_TERM_YEARS)

    def test_cash_the_loans_repaid_beyond_the_reserve_goes_back_to_the_depositors(self):
        record, bank, loan = bank_that_has_lent()
        record.loans.remove(loan)                    # the borrower repaid in full
        record.book.transfer(Transfer(BORROWER, BANK, MONEY, 820.0, "repaid"))
        bank_service.service_deposits(record, MONEY, 1)
        self.assertLess(banks.owed_to_depositors(record, BANK), 900.0)
        self.assertGreaterEqual(balance(record, BANK), bank.reserve_share * banks.owed_to_depositors(record, BANK) - 1e-6)


class Failure(unittest.TestCase):
    def test_a_default_smaller_than_the_capital_leaves_the_bank_standing(self):
        record, bank, loan = bank_that_has_lent()
        loan.principal -= 50.0                            # a default of 50 against 100 of capital
        self.assertGreater(banks.capital_of(record, BANK, MONEY), 0.0)
        self.assertEqual(banks.run_on_insolvent(record, MONEY, 1), [])
        self.assertLess(bank.failed_year, 0)

    def test_a_default_beyond_the_capital_fails_the_bank(self):
        record, bank, loan = bank_that_has_lent()
        record.loans.remove(loan)                    # the borrower defaulted on the whole loan
        self.assertLess(banks.capital_of(record, BANK, MONEY), 0.0)
        self.assertEqual(banks.run_on_insolvent(record, MONEY, 1), [BANK])
        self.assertEqual(bank.failed_year, 1)
        self.assertEqual([deposit_loan.years_left for deposit_loan in banks.deposits_of(record, BANK)], [1.0, 1.0])

    def test_a_failed_banks_depositors_share_what_it_holds_and_bear_the_loss(self):
        record, bank, loan = bank_that_has_lent()
        record.loans.remove(loan)
        banks.run_on_insolvent(record, MONEY, 1)
        supply, cash = record.book.money_supply(MONEY), balance(record, BANK)
        before = {depositor: balance(record, depositor) for depositor in DEPOSITORS}
        bank_service.service_deposits(record, MONEY, 1)
        paid = {depositor: balance(record, depositor) - before[depositor] for depositor in DEPOSITORS}
        self.assertAlmostEqual(sum(paid.values()), cash)                     # all it held went to them, in proportion
        self.assertAlmostEqual(paid[DEPOSITORS[0]], paid[DEPOSITORS[1]])
        for depositor in DEPOSITORS:
            self.assertGreater(record.credit_losses.get(depositor, 0.0), 0.0)
            self.assertAlmostEqual(credit_claims.claims_by_lender(record.loans, MONEY).get(depositor, 0.0), 0.0)
        self.assertAlmostEqual(record.book.money_supply(MONEY), supply)

    def test_the_founder_loses_the_capital_before_the_depositors_lose_anything(self):
        record, _bank, loan = bank_that_has_lent()
        loan.principal -= 100.0                           # a default of exactly the capital: the deposits are still covered
        self.assertAlmostEqual(banks.capital_of(record, BANK, MONEY), 0.0)
        self.assertEqual(banks.run_on_insolvent(record, MONEY, 1), [])
        self.assertEqual(record.credit_losses.get(DEPOSITORS[0], 0.0), 0.0)

    def test_a_failed_bank_takes_no_more_deposits_and_offers_nothing(self):
        record, bank, _loan = bank_that_has_lent()
        bank.failed_year = 1
        owed = banks.owed_to_depositors(record, BANK)
        offers = [FundsOffer(depositor, MONEY, 50.0, 0.03) for depositor in DEPOSITORS]
        remaining, pledged = banks.intermediate(SETUP, record, offers, 2, ())
        self.assertEqual(remaining, offers)
        self.assertEqual(pledged, {})
        self.assertEqual(banks.owed_to_depositors(record, BANK), owed)


class Dividends(unittest.TestCase):
    def capital_only_bank(self):
        """A bank holding just its founder's capital, 50 of it lent to a producer: no deposits."""
        record = record_with(household_cash())
        bank = standing_bank(record)
        record.book.transfer(Transfer(BANK, BORROWER, MONEY, 50.0, "loan"))
        record.loans.append(new_loan(50.0))
        return record, bank

    def serviced(self, record):
        """service_deposits with the founder's dividend booked as paid, un-shared (sharing it on is ownership.spread's)."""
        with mock.patch.object(bank_service.ownership, "spread", lambda _record, payments: payments):
            bank_service.service_deposits(record, MONEY, 1)

    def test_a_bank_that_earned_nothing_beyond_its_capital_pays_the_founder_nothing(self):
        record, _bank = self.capital_only_bank()
        before = balance(record, FOUNDER)
        self.serviced(record)
        self.assertAlmostEqual(balance(record, FOUNDER), before)

    def test_the_founder_is_paid_only_what_the_bank_earned_beyond_its_capital(self):
        record, bank = self.capital_only_bank()
        record.book.transfer(Transfer(FOUNDER, BANK, MONEY, 30.0, "earnings"))
        before = balance(record, FOUNDER)
        self.serviced(record)
        self.assertAlmostEqual(balance(record, FOUNDER) - before, 30.0)
        self.assertGreaterEqual(banks.capital_of(record, BANK, MONEY), bank.paid_in - 1e-6)


if __name__ == "__main__":
    unittest.main()
