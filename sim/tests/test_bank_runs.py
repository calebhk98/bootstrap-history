"""Complaint 106: depositors withdraw from a bank whose loss record threatens their deposit (their interest does not
cover the loss they expect after its capital); the bank pays from its cash, sells loans at the secondary price when it
is short, and fails when it cannot, the depositors bearing the loss through the one default rule and the founder
losing its capital. Rules on a bank built by hand."""

QUICK_TOPIC = True

from sim.economy import bank_runs, bank_service, banks, secondary_trade
from sim.economy.secondary_trade import BOND_MARKET
from sim.economy.types import EDGE_MINT, FundsOffer, Transfer
from sim.tests import test_economy_banks as bank_fixtures

MARKET_RATE = 0.05


class RunFixture(bank_fixtures.BankFixture):
    def setUp(self):
        super().setUp()
        self.bank, self.loan = self.stand_a_bank_that_has_lent()
        self.loan.collateral_value = 100000.0         # a loan the savers see as well secured
        self.deposits = banks.deposits_of(self.record, self.bank.agent_id)
        self.buyer = sorted(self.record.cohorts)[3]
        self.record.book.transfer(Transfer(EDGE_MINT, self.buyer, self.money, 2000.0, "test coin"))   # the saver's pledge (households open with no spare cash)
        self.supply = self.record.book.money_supply(self.money)

    def expect_losses(self, rate):
        self.record.loss_rates[self.bank.agent_id] = rate

    def savers(self, amount=2000.0, rate=0.04):
        return [FundsOffer(self.buyer, self.money, amount, rate)]

    def run_bank(self, offers=None, institutions=()):
        return bank_runs.run(self.setup, self.record, self.savers() if offers is None else offers, 1, institutions, MARKET_RATE)

    def capital(self):
        return banks.capital_of(self.record, self.bank.agent_id, self.money)


class WhoWithdraws(RunFixture):
    def test_a_bank_with_no_loss_record_is_not_run_on(self):
        self.assertEqual(bank_runs.expected_loss_share(self.record, self.bank, self.money), 0.0)
        self.assertEqual(bank_runs.withdrawing(self.record, self.bank, self.money), [])

    def test_the_loss_the_capital_covers_makes_no_depositor_withdraw(self):
        self.expect_losses(0.10)                 # 82 of loss expected against 100 of capital
        self.assertEqual(bank_runs.withdrawing(self.record, self.bank, self.money), [])

    def test_a_loss_beyond_the_capital_falls_on_the_depositors_as_a_share_of_what_the_bank_owes(self):
        self.expect_losses(0.20)
        share = bank_runs.expected_loss_share(self.record, self.bank, self.money)
        self.assertAlmostEqual(share, (0.20 * 820.0 - 100.0) / 900.0)

    def test_depositors_whose_interest_covers_the_expected_loss_stay_and_the_rest_withdraw(self):
        self.expect_losses(0.20)
        patient, hasty = self.deposits[0], self.deposits[1]
        patient.rate, hasty.rate = 0.10, 0.01
        self.assertEqual(bank_runs.withdrawing(self.record, self.bank, self.money), [hasty])

    def test_a_worse_record_sends_more_depositors_to_the_door(self):
        self.deposits[0].rate, self.deposits[1].rate = 0.05, 0.10
        self.expect_losses(0.17)
        mild = len(bank_runs.withdrawing(self.record, self.bank, self.money))
        self.expect_losses(0.30)
        severe = len(bank_runs.withdrawing(self.record, self.bank, self.money))
        self.assertLess(mild, severe)

    def test_a_thinner_capital_makes_the_same_record_more_threatening(self):
        self.expect_losses(0.20)
        before = bank_runs.expected_loss_share(self.record, self.bank, self.money)
        self.record.book.transfer(Transfer(self.bank.agent_id, self.founder, self.money, 60.0, "capital withdrawn"))
        self.assertGreater(bank_runs.expected_loss_share(self.record, self.bank, self.money), before)


class PayingTheWithdrawals(RunFixture):
    def setUp(self):
        super().setUp()
        self.expect_losses(0.20)
        self.deposits[0].rate, self.deposits[1].rate = 0.10, 0.01      # one stays, one withdraws 450
        self.leaver, self.stayer = self.deposits[1], self.deposits[0]

    def test_a_bank_with_the_cash_pays_the_leaver_in_full_and_stands(self):
        self.loan.principal -= 600.0                 # the borrower repaid 600, so the bank holds the cash with no change in capital
        self.record.book.transfer(Transfer(self.borrower, self.bank.agent_id, self.money, 600.0, "repaid"))
        self.expect_losses(0.60)
        before = self.balance(self.leaver.lender)
        self.run_bank()
        self.assertAlmostEqual(self.balance(self.leaver.lender) - before, 450.0)
        self.assertLess(self.bank.failed_year, 0)
        self.assertEqual(sorted(deposit.lender for deposit in banks.deposits_of(self.record, self.bank.agent_id)),
                         [self.stayer.lender])
        self.assertAlmostEqual(self.record.book.money_supply(self.money), self.supply)

    def test_a_bank_short_of_cash_sells_loans_to_savers_at_a_price_below_what_they_are_worth_to_it(self):
        capital = self.capital()
        offers = self.run_bank(offers=self.savers(rate=0.09), institutions=(BOND_MARKET,))
        self.assertLess(self.bank.failed_year, 0)
        self.assertEqual(banks.owed_to_depositors(self.record, self.bank.agent_id), 450.0)
        self.assertLess(self.capital(), capital)                        # the loans went for less than they were worth to it
        self.assertLess(offers[0].amount, 2000.0)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), self.supply)
        sold = [loan for loan in self.record.loans if loan.lender == self.buyer]
        self.assertTrue(sold)

    def test_the_price_the_bank_gets_falls_when_savers_ask_more(self):
        cheap_offers = self.run_bank(offers=self.savers(rate=0.04), institutions=(BOND_MARKET,))
        spent_cheap = 2000.0 - cheap_offers[0].amount
        sold_cheap = sum(loan.principal for loan in self.record.loans if loan.lender == self.buyer)
        self.setUp()
        dear_offers = self.run_bank(offers=self.savers(rate=0.12), institutions=(BOND_MARKET,))
        spent_dear = 2000.0 - dear_offers[0].amount
        sold_dear = sum(loan.principal for loan in self.record.loans if loan.lender == self.buyer)
        self.assertGreater(spent_cheap / sold_cheap, spent_dear / sold_dear)

    def test_without_a_market_for_loans_the_bank_fails_and_pays_the_leaver_what_it_holds(self):
        cash = self.balance(self.bank.agent_id)
        before = self.balance(self.leaver.lender)
        self.run_bank(institutions=())
        self.assertAlmostEqual(self.balance(self.leaver.lender) - before, cash)
        self.assertEqual(self.bank.failed_year, 1)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), self.supply)

    def test_savers_who_cannot_pay_enough_leave_the_bank_to_fail(self):
        self.run_bank(offers=self.savers(amount=10.0), institutions=(BOND_MARKET,))
        self.assertEqual(self.bank.failed_year, 1)

    def test_a_failed_bank_s_depositors_bear_the_loss_through_the_default_rule(self):
        self.run_bank(institutions=())
        for deposit in banks.deposits_of(self.record, self.bank.agent_id):
            self.assertEqual(deposit.years_left, 1.0)
        bank_service.service_deposits(self.record, self.money, 2)
        lost = self.record.credit_losses.get(self.leaver.lender, 0.0) + self.record.credit_losses.get(self.stayer.lender, 0.0)
        self.assertGreater(lost, 0.0)

    def test_the_founder_loses_the_capital_the_failed_bank_no_longer_holds(self):
        self.loan.principal -= 300.0               # a default that leaves the bank short of what it owes
        self.run_bank(institutions=())
        self.assertGreater(self.bank.owner_loss, 0.0)
        self.assertLessEqual(self.bank.owner_loss, self.bank.paid_in)

    def test_a_bank_that_kept_every_deposit_in_reserve_pays_all_who_leave_and_sells_nothing(self):
        self.bank.reserve_share = 1.0
        self.record.book.transfer(Transfer(self.borrower, self.bank.agent_id, self.money, 820.0, "repaid in full"))
        self.record.loans.remove(self.loan)
        self.run_bank(institutions=(BOND_MARKET,))
        self.assertLess(self.bank.failed_year, 0)
        self.assertEqual([loan for loan in self.record.loans if loan.lender == self.buyer], [])


class Saved(RunFixture):
    def test_the_owner_s_loss_is_saved_with_the_bank(self):
        from sim.economy.record import EconomyRecord
        self.bank.owner_loss = 12.5
        loaded = EconomyRecord.from_record(self.record.to_record())
        self.assertEqual(loaded.banks[self.bank.agent_id].owner_loss, 12.5)


if __name__ == "__main__":
    import unittest
    unittest.main()
