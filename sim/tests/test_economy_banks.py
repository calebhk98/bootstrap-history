"""Complaint 106: a bank is an agent. Households pledge their savings to it, it lends them on and takes the deposit
as it lends, it keeps a reserve and earns a margin, and it fails when its loans default beyond its capital: its
depositors run, and they bear the loss through the one default rule. A society without the institution founds no
bank."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import bank_service, banks, credit_claims
from sim.economy.economy import Economy
from sim.economy.record import EconomyRecord
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


class DepositsAndLending(BankFixture):
    def test_the_bank_offers_its_free_cash_and_what_its_depositors_pledge_less_the_reserve_it_must_keep(self):
        bank, remaining, pledged = self.stand_a_bank()
        self.assertEqual([offer.lender for offer in remaining], [bank.agent_id])
        self.assertAlmostEqual(remaining[0].amount, CAPITAL + (1.0 - bank.reserve_share) * 2 * PLEDGED)
        self.assertEqual(sorted(offer.lender for offer in pledged[bank.agent_id]), self.depositors)

    def test_a_deposit_exists_only_for_a_loan_the_bank_made_and_keeps_the_reserve(self):
        supply = self.record.book.money_supply(self.money)
        bank, _remaining, pledged = self.stand_a_bank()
        self.assertEqual(banks.owed_to_depositors(self.record, bank.agent_id), 0.0)
        self.bank_lends(bank, pledged, 820.0)
        deposits = banks.owed_to_depositors(self.record, bank.agent_id)
        self.assertAlmostEqual(deposits, 900.0)      # 100 of its own, the other 720 from deposits that leave a fifth as reserve
        self.assertAlmostEqual(self.balance(bank.agent_id), bank.reserve_share * deposits)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), supply)

    def test_a_smaller_loan_takes_a_smaller_deposit(self):
        bank, _remaining, pledged = self.stand_a_bank()
        self.bank_lends(bank, pledged, 300.0)
        self.assertAlmostEqual(banks.owed_to_depositors(self.record, bank.agent_id), (300.0 - CAPITAL) / (1.0 - bank.reserve_share))

    def test_a_loan_the_banks_own_cash_covers_takes_no_deposit(self):
        bank, _remaining, pledged = self.stand_a_bank()
        self.bank_lends(bank, pledged, 50.0)
        self.assertEqual(banks.owed_to_depositors(self.record, bank.agent_id), 0.0)

    def test_a_deposit_is_the_depositors_claim_and_the_banks_debt(self):
        bank, _loan = self.stand_a_bank_that_has_lent()
        claims = credit_claims.claims_by_lender(self.record.loans, self.money)
        debts = credit_claims.debts_by_borrower(self.record.loans, self.money)
        for depositor in self.depositors:
            self.assertAlmostEqual(claims[depositor], 450.0)
        self.assertAlmostEqual(debts[bank.agent_id], 900.0)

    def test_a_bank_with_capital_and_no_losses_asks_what_it_pays_depositors(self):
        bank, remaining, _pledged = self.stand_a_bank()
        self.assertAlmostEqual(banks.spread_of(self.record, bank, self.money), 0.0)
        self.assertAlmostEqual(remaining[0].minimum_rate, 0.03)

    def test_a_society_without_the_institution_founds_no_bank(self):
        offers = [FundsOffer(depositor, self.money, PLEDGED, 0.03) for depositor in self.depositors]
        remaining, pledged = banks.intermediate(self.setup, self.record, offers, 0, ())
        self.assertEqual(self.record.banks, {})
        self.assertEqual(remaining, offers)
        self.assertEqual(pledged, {})

    def test_a_society_with_it_has_the_richest_household_found_one(self):
        offers = [FundsOffer(depositor, self.money, PLEDGED, 0.03) for depositor in self.depositors]
        banks.intermediate(self.setup, self.record, offers, 0, INSTITUTIONS)
        self.assertEqual(len(self.record.banks), 1)
        self.assertGreater(self.balance(next(iter(self.record.banks))), 0.0)

    def test_the_bank_pays_its_depositors_their_rate_out_of_what_it_holds(self):
        self.stand_a_bank_that_has_lent()
        before = {depositor: self.balance(depositor) for depositor in self.depositors}
        received = bank_service.service_deposits(self.record, self.money, 1)
        for depositor in self.depositors:
            self.assertAlmostEqual(received[depositor], 450.0 * 0.03)
            self.assertAlmostEqual(self.balance(depositor) - before[depositor], 450.0 * 0.03 + 450.0 / banks.DEPOSIT_TERM_YEARS)

    def test_cash_the_loans_repaid_beyond_the_reserve_goes_back_to_the_depositors(self):
        bank, loan = self.stand_a_bank_that_has_lent()
        self.record.loans.remove(loan)                    # the borrower repaid in full
        self.record.book.transfer(Transfer(self.borrower, bank.agent_id, self.money, 820.0, "repaid"))
        bank_service.service_deposits(self.record, self.money, 1)
        self.assertLess(banks.owed_to_depositors(self.record, bank.agent_id), 900.0)
        self.assertGreaterEqual(self.balance(bank.agent_id), bank.reserve_share * banks.owed_to_depositors(self.record, bank.agent_id) - 1e-6)

    def test_the_bank_is_saved_with_the_record(self):
        self.stand_a_bank_that_has_lent()
        loaded = EconomyRecord.from_record(self.record.to_record())
        self.assertEqual(loaded.banks, self.record.banks)


class Failure(BankFixture):
    def test_a_default_smaller_than_the_capital_leaves_the_bank_standing(self):
        bank, loan = self.stand_a_bank_that_has_lent()
        loan.principal -= 50.0                            # a default of 50 against 100 of capital
        self.assertGreater(banks.capital_of(self.record, bank.agent_id, self.money), 0.0)
        self.assertEqual(banks.run_on_insolvent(self.record, self.money, 1), [])
        self.assertLess(bank.failed_year, 0)

    def test_a_default_beyond_the_capital_fails_the_bank_and_the_depositors_bear_the_loss(self):
        supply = self.record.book.money_supply(self.money)
        bank, loan = self.stand_a_bank_that_has_lent()
        self.record.loans.remove(loan)                    # the borrower defaulted on the whole loan
        cash = self.balance(bank.agent_id)
        self.assertLess(banks.capital_of(self.record, bank.agent_id, self.money), 0.0)
        before = {depositor: self.balance(depositor) for depositor in self.depositors}
        self.assertEqual(banks.run_on_insolvent(self.record, self.money, 1), [bank.agent_id])
        bank_service.service_deposits(self.record, self.money, 1)
        paid = {depositor: self.balance(depositor) - before[depositor] for depositor in self.depositors}
        self.assertAlmostEqual(sum(paid.values()), cash)                     # all it held went to them, in proportion
        self.assertAlmostEqual(paid[self.depositors[0]], paid[self.depositors[1]])
        for depositor in self.depositors:
            self.assertGreater(self.record.credit_losses.get(depositor, 0.0), 0.0)
            self.assertAlmostEqual(credit_claims.claims_by_lender(self.record.loans, self.money).get(depositor, 0.0), 0.0)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), supply)

    def test_the_founder_loses_the_capital_before_the_depositors_lose_anything(self):
        bank, loan = self.stand_a_bank_that_has_lent()
        loan.principal -= 100.0                           # a default of exactly the capital: the deposits are still covered
        self.assertAlmostEqual(banks.capital_of(self.record, bank.agent_id, self.money), 0.0)
        self.assertEqual(banks.run_on_insolvent(self.record, self.money, 1), [])
        self.assertEqual(self.record.credit_losses.get(self.depositors[0], 0.0), 0.0)

    def test_a_failed_bank_takes_no_more_deposits_and_offers_nothing(self):
        bank, _loan = self.stand_a_bank_that_has_lent()
        bank.failed_year = 1
        owed = banks.owed_to_depositors(self.record, bank.agent_id)
        offers = [FundsOffer(depositor, self.money, 50.0, 0.03) for depositor in self.depositors]
        remaining, pledged = banks.intermediate(self.setup, self.record, offers, 2, ())
        self.assertEqual(remaining, offers)
        self.assertEqual(pledged, {})
        self.assertEqual(banks.owed_to_depositors(self.record, bank.agent_id), owed)


class Dividends(BankFixture):
    def test_the_founder_is_paid_only_what_the_bank_earned_beyond_its_capital(self):
        bank, _loan = self.stand_a_bank_that_has_lent(amount=50.0)       # no deposits: just the capital, lent in part
        before = sum(self.balance(cohort) for cohort in self.record.cohorts)
        bank_service.service_deposits(self.record, self.money, 1)
        self.assertAlmostEqual(sum(self.balance(cohort) for cohort in self.record.cohorts), before)    # nothing earned, nothing paid
        self.record.book.transfer(Transfer(self.founder, bank.agent_id, self.money, 30.0, "test earnings"))
        before = sum(self.balance(cohort) for cohort in self.record.cohorts)
        bank_service.service_deposits(self.record, self.money, 1)
        self.assertAlmostEqual(sum(self.balance(cohort) for cohort in self.record.cohorts) - before, 30.0)
        self.assertGreaterEqual(banks.capital_of(self.record, bank.agent_id, self.money), bank.paid_in - 1e-6)


class InTheYearLoop(unittest.TestCase):
    def test_a_society_with_the_institution_gets_a_bank_and_money_stays_conserved(self):
        setup = fixture.small_setup()
        economy = Economy(setup)
        outcomes = [economy.step(dataclasses.replace(fixture.quiet_year(setup), institutions=INSTITUTIONS))
                    for _year in range(4)]
        self.assertEqual(len(economy.record.banks), 1)
        for outcome in outcomes:
            self.assertAlmostEqual(outcome.conservation_residual, 0.0, places=6)

    def test_a_society_without_it_gets_none(self):
        setup = fixture.small_setup()
        economy = Economy(setup)
        economy.step(fixture.quiet_year(setup))
        self.assertEqual(economy.record.banks, {})


if __name__ == "__main__":
    unittest.main()
