"""Complaint 106: a state (any actor with a purse) insures deposits for a premium equal to the payout expected and pays
depositors when a bank fails, and lends as a last resort to a solvent bank facing a run at the market rate plus the
bank's default risk, against its loans. Each rule is called on a record written out in the test."""

QUICK_TOPIC = True

import unittest

from sim.economy import bank_runs, banks, deposit_insurance, last_resort
from sim.economy.types import EDGE_MINT, Transfer
from sim.tests import test_economy_banks as fixtures

STATE = "state:0"
MONEY = fixtures.MONEY
BANK = fixtures.BANK
DEPOSITORS = fixtures.DEPOSITORS
SETUP = fixtures.SETUP


def state_record(reserve):
    """(record, bank): two depositors with 450 each in a bank that has lent 820 and holds 130 of cash, and a state holding `reserve`
    that insures the bank's deposits."""
    record, bank, _loan = fixtures.bank_that_has_lent()
    record.book.transfer(Transfer(EDGE_MINT, STATE, MONEY, reserve, "state purse"))
    record.capital_markets.deposit_insurer = STATE
    record.capital_markets.last_resort = None
    record.capital_markets.last_resort_issues = False
    return record, bank


class Premium(unittest.TestCase):
    def test_the_premium_is_the_share_expected_lost_times_the_deposits(self):
        self.assertAlmostEqual(deposit_insurance.premium(0.04, 900.0), 36.0)

    def test_a_bank_expected_to_lose_nothing_beyond_its_capital_pays_nothing(self):
        self.assertEqual(deposit_insurance.premium(0.0, 900.0), 0.0)

    def test_the_bank_pays_what_it_owes_up_to_its_cash(self):
        record, _bank = state_record(1.0)
        cash = record.book.balance(BANK, MONEY)
        paid = deposit_insurance.collect(record, BANK, 5000.0, MONEY)
        self.assertAlmostEqual(paid, cash)
        self.assertAlmostEqual(record.book.balance(STATE, MONEY), 1.0 + cash)


class Cover(unittest.TestCase):
    def test_no_payout_expected_is_full_trust(self):
        self.assertEqual(deposit_insurance.cover(0.0, 0.0), 1.0)

    def test_a_reserve_half_the_payout_expected_is_half_trusted(self):
        self.assertAlmostEqual(deposit_insurance.cover(50.0, 100.0), 0.5)

    def test_a_reserve_beyond_the_payout_is_trusted_fully(self):
        self.assertEqual(deposit_insurance.cover(500.0, 100.0), 1.0)


class Payout(unittest.TestCase):
    def test_depositors_are_paid_in_full_when_the_reserve_lasts_and_the_state_takes_their_claims(self):
        record, _bank = state_record(2000.0)
        before = [record.book.balance(depositor, MONEY) for depositor in DEPOSITORS]
        paid = deposit_insurance.settle(record, BANK, MONEY)
        self.assertAlmostEqual(paid, 900.0)
        for depositor, was in zip(DEPOSITORS, before):
            self.assertAlmostEqual(record.book.balance(depositor, MONEY), was + fixtures.PLEDGED)
        self.assertAlmostEqual(sum(deposit.principal for deposit in record.credit.loans.select(lender=STATE)), 900.0)
        self.assertEqual(len(record.credit.loans.select(lender=DEPOSITORS[0])), 0)

    def test_a_short_reserve_pays_every_depositor_the_same_share_and_leaves_them_the_rest(self):
        record, _bank = state_record(450.0)
        before = [record.book.balance(depositor, MONEY) for depositor in DEPOSITORS]
        deposit_insurance.settle(record, BANK, MONEY)
        for depositor, was in zip(DEPOSITORS, before):
            self.assertAlmostEqual(record.book.balance(depositor, MONEY), was + 225.0)
            self.assertAlmostEqual(sum(deposit.principal for deposit in record.credit.loans.select(lender=depositor)), 225.0)

    def test_nothing_is_paid_when_no_one_insures(self):
        record, _bank = state_record(2000.0)
        record.capital_markets.deposit_insurer = None
        self.assertEqual(deposit_insurance.settle(record, BANK, MONEY), 0.0)

    def test_a_bank_that_fails_pays_its_depositors_through_the_insurer(self):
        record, bank = state_record(2000.0)
        before = record.book.balance(DEPOSITORS[0], MONEY)
        banks.fail(record, bank, 1, MONEY)
        self.assertAlmostEqual(record.book.balance(DEPOSITORS[0], MONEY), before + fixtures.PLEDGED)


class DepositorsRun(unittest.TestCase):
    def test_a_funded_insurer_keeps_the_depositors_from_withdrawing(self):
        record, bank = state_record(1000.0)
        record.credit.loss_rates[BANK] = 0.20
        for deposit in banks.deposits_of(record, BANK):
            deposit.rate = 0.0
        self.assertAlmostEqual(bank_runs.insured_cover(record, MONEY), 1.0)
        self.assertEqual(bank_runs.withdrawing(record, bank, MONEY), [])

    def test_without_an_insurer_the_same_depositors_withdraw(self):
        record, bank = state_record(1000.0)
        record.capital_markets.deposit_insurer = None
        record.credit.loss_rates[BANK] = 0.20
        for deposit in banks.deposits_of(record, BANK):
            deposit.rate = 0.0
        self.assertEqual(len(bank_runs.withdrawing(record, bank, MONEY)), 2)


class LastResort(unittest.TestCase):
    def test_the_penalty_rate_is_the_market_rate_plus_the_default_risk(self):
        self.assertAlmostEqual(last_resort.penalty_rate(0.05, 0.03), 0.08)

    def test_the_advance_is_what_the_collateral_covers_with_a_years_interest(self):
        self.assertAlmostEqual(last_resort.lendable(1080.0, 0.08, 5000.0), 1000.0)
        self.assertAlmostEqual(last_resort.lendable(1080.0, 0.08, 400.0), 400.0)

    def test_a_solvent_bank_borrows_at_the_penalty_rate_from_the_lenders_purse(self):
        record, _bank = state_record(300.0)
        cash = record.book.balance(BANK, MONEY)
        advance = last_resort.lend(record, STATE, False, BANK, 200.0, 0.05, 0.03, 1, MONEY)
        self.assertIsNone(advance.refusal)
        self.assertAlmostEqual(advance.loan.principal, 200.0)
        self.assertAlmostEqual(advance.loan.rate, 0.08)
        self.assertAlmostEqual(record.book.balance(STATE, MONEY), 100.0)
        self.assertAlmostEqual(record.book.balance(BANK, MONEY), cash + 200.0)

    def test_the_lender_cannot_lend_more_than_its_purse_unless_it_issues_money(self):
        record, _bank = state_record(50.0)
        self.assertAlmostEqual(last_resort.lend(record, STATE, False, BANK, 200.0, 0.05, 0.0, 1, MONEY).loan.principal, 50.0)
        record, _bank = state_record(50.0)
        supply = record.book.money_supply(MONEY)
        self.assertAlmostEqual(last_resort.lend(record, STATE, True, BANK, 200.0, 0.05, 0.0, 1, MONEY).loan.principal, 200.0)
        self.assertAlmostEqual(record.book.money_supply(MONEY), supply + 200.0)

    def test_an_insolvent_bank_is_refused(self):
        record, _bank = state_record(300.0)
        record.book.transfer(Transfer(BANK, EDGE_MINT, MONEY, record.book.balance(BANK, MONEY), "bank cash lost"))
        record.credit.loans.select(lender=BANK)[0].principal = 10.0
        advance = last_resort.lend(record, STATE, False, BANK, 200.0, 0.05, 0.0, 1, MONEY)
        self.assertIsNone(advance.loan)
        self.assertEqual(advance.refusal.cause, "bank_insolvent")

    def test_a_run_is_met_from_the_last_resort_and_the_bank_stands(self):
        record, _bank = state_record(3000.0)
        record.capital_markets.deposit_insurer = None
        record.capital_markets.last_resort = STATE
        record.credit.loss_rates[BANK] = 0.20
        for deposit in banks.deposits_of(record, BANK):
            deposit.rate = 0.0
        bank_runs.run(SETUP, record, [], 1, (), 0.05)
        self.assertLess(record.capital_markets.banks[BANK].failed_year, 0)
        self.assertTrue(any(loan.lender == STATE for loan in record.credit.loans.select(borrower=BANK)))
