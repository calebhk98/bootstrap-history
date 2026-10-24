"""A bank standing in a fixture economy, for the scenario tests that build on one (test_bank_runs)."""
import unittest

from sim.economy import banks
from sim.economy.economy import Economy
from sim.economy.types import FundsOffer, Loan, Transfer
from sim.tests import economy_fixture as fixture

INSTITUTIONS = (banks.DEPOSIT_BANKING,)
CAPITAL = 100.0
PLEDGED = 450.0         # by each of two depositors


class BankFixture(unittest.TestCase):
    def setUp(self):
        self.economy = Economy(fixture.small_setup())
        self.setup = self.economy.setup
        self.record = self.economy.record
        self.money = self.setup.currency_id
        self.depositors = sorted(self.record.cohorts)[1:3]
        self.founder = sorted(self.record.cohorts)[0]
        self.borrower = sorted(self.record.producers)[0]

    def balance(self, agent):
        return self.record.book.balance(agent, self.money)

    def stand_a_bank(self):
        """A bank with its founder's capital, and the offers its depositors pledge to it."""
        bank = banks.found(self.record, self.founder, CAPITAL, 0, self.money)
        offers = [FundsOffer(depositor, self.money, PLEDGED, 0.03) for depositor in self.depositors]
        remaining, pledged = banks.intermediate(self.setup, self.record, offers, 0, INSTITUTIONS)
        return bank, remaining, pledged

    def bank_lends(self, bank, pledged, amount):
        """The bank makes a loan of `amount` to a producer, taking the deposits it needs first."""
        loan = Loan("loan:0:0", bank.agent_id, self.borrower, self.money, amount, rate=0.05, years_left=5.0,
                    issued_year=0)
        banks.draw_deposits(self.record, [loan], pledged, 0, self.money)
        self.record.book.transfer(Transfer(bank.agent_id, self.borrower, self.money, amount, "test loan"))
        self.record.loans.append(loan)
        return loan

    def stand_a_bank_that_has_lent(self, amount=820.0):
        bank, _remaining, pledged = self.stand_a_bank()
        return bank, self.bank_lends(bank, pledged, amount)
