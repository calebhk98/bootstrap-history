"""Complaint 106: insurance against a hazard the model has (a poor harvest, read from the year's weather). A premium
comes from the hazard's own record (its mean loss and its worst year at the market rate), a mutual charges nothing in
advance and its members pay the claims between them, a company fails when the year's claims outrun its purse, and a
holder buys cover only when its own cash would not bear the worst year. Rules on the economy's record built by hand."""

QUICK_TOPIC = True

import unittest

from sim.economy import insurance
from sim.economy.accounts import Book
from sim.economy.insurance import HARVEST
from sim.economy.market_memory import MarketMemory
from sim.economy.record import EconomyRecord
from sim.economy.types import CurrencySpec, Transfer

MARKET_RATE = 0.05
MONEY = "coin"
AGENTS = ("agent:a", "agent:b", "agent:c")      # the founder, a holder and another holder, each with cash in the book
CASH = 1000.0


class InsuranceFixture(unittest.TestCase):
    def setUp(self):
        self.record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec(MONEY, "fiat", None, 0.0, None))
        self.state = self.record.capital
        self.money = MONEY
        self.founder, self.holder, self.other = AGENTS
        for agent in AGENTS:
            self.record.book.transfer(Transfer("edge:legacy", agent, MONEY, CASH, "opening"))
        self.supply = self.record.book.money_supply(self.money)

    def balance(self, agent):
        return self.record.book.balance(agent, self.money)

    def watch(self, *loss_shares):
        for share in loss_shares:
            insurance.observe(self.state, HARVEST, share)

    def company(self, capital=300.0):
        return insurance.found(self.record, self.founder, capital, 0, self.money)


class Pricing(InsuranceFixture):
    def test_a_year_of_weather_below_normal_took_that_share_and_better_than_normal_took_none(self):
        self.assertAlmostEqual(insurance.loss_share_of(0.8), 0.2)
        self.assertEqual(insurance.loss_share_of(1.15), 0.0)
        self.assertEqual(insurance.loss_share_of(-1.0), 1.0)

    def test_without_a_record_of_the_hazard_nothing_is_priced(self):
        self.assertIsNone(insurance.expected_loss_share(self.state, HARVEST))
        self.assertIsNone(insurance.premium_rate(self.state, HARVEST, MARKET_RATE))

    def test_the_expected_loss_is_the_mean_share_taken_over_the_years_watched(self):
        self.watch(0.0, 0.2, 0.0, 0.1)
        self.assertAlmostEqual(insurance.expected_loss_share(self.state, HARVEST), 0.075)

    def test_the_premium_is_the_expected_claims_plus_the_return_on_capital_held_for_the_worst_year(self):
        self.watch(0.0, 0.2, 0.0, 0.1)
        self.assertAlmostEqual(insurance.premium_rate(self.state, HARVEST, MARKET_RATE), 0.075 + MARKET_RATE * (0.2 - 0.075))

    def test_a_dearer_market_rate_raises_the_premium_when_a_bad_year_has_been_seen(self):
        self.watch(0.0, 0.3)
        self.assertGreater(insurance.premium_rate(self.state, HARVEST, 0.10), insurance.premium_rate(self.state, HARVEST, 0.02))

    def test_a_bad_season_raises_the_premium_and_good_ones_lower_it(self):
        self.watch(0.0, 0.0)
        calm = insurance.premium_rate(self.state, HARVEST, MARKET_RATE)
        self.watch(0.4)
        bad = insurance.premium_rate(self.state, HARVEST, MARKET_RATE)
        self.watch(*([0.0] * 10))
        recovered = insurance.premium_rate(self.state, HARVEST, MARKET_RATE)
        self.assertGreater(bad, calm)
        self.assertLess(recovered, bad)

    def test_a_holder_buys_cover_only_when_its_cash_would_not_bear_the_worst_year_and_the_cover_costs_less_than_it(self):
        self.watch(0.0, 0.3)
        rate = insurance.premium_rate(self.state, HARVEST, MARKET_RATE)
        self.assertTrue(insurance.wants_cover(10.0, 100.0, rate, self.state, HARVEST))
        self.assertFalse(insurance.wants_cover(500.0, 100.0, rate, self.state, HARVEST))      # it can bear 30 itself
        self.assertFalse(insurance.wants_cover(10.0, 100.0, 0.5, self.state, HARVEST))        # the premium is dearer than the loss
        self.assertFalse(insurance.wants_cover(10.0, 100.0, None, self.state, "unwatched"))


class ACompany(InsuranceFixture):
    def test_a_company_holds_its_founders_capital_and_the_book_is_conserved(self):
        insurer = self.company(300.0)
        self.assertAlmostEqual(self.balance(insurer.agent_id), 300.0)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), self.supply)

    def test_a_founder_without_the_capital_founds_nothing(self):
        self.assertIsNone(insurance.found(self.record, "nobody", 100.0, 0, self.money))

    def test_the_holder_pays_the_premium_the_hazard_s_record_gives_and_the_company_receives_it(self):
        self.watch(0.0, 0.2)
        insurer = self.company()
        insurance.insure(self.state, insurer.agent_id, self.holder, HARVEST, 100.0)
        before = self.balance(self.holder)
        paid = insurance.collect_premiums(self.record, self.money, MARKET_RATE)
        expected = 100.0 * insurance.premium_rate(self.state, HARVEST, MARKET_RATE)
        self.assertAlmostEqual(paid[self.holder], expected)
        self.assertAlmostEqual(before - self.balance(self.holder), expected)
        self.assertAlmostEqual(self.balance(insurer.agent_id), 300.0 + expected)

    def test_a_holder_who_cannot_pay_the_premium_loses_its_cover(self):
        self.watch(0.0, 0.2)
        insurer = self.company()
        insurance.insure(self.state, insurer.agent_id, "nobody:without cash", HARVEST, 100.0)
        self.assertEqual(insurance.collect_premiums(self.record, self.money, MARKET_RATE), {})
        self.assertEqual(self.state.policies, [])

    def test_the_company_pays_the_share_of_the_insured_value_the_year_took(self):
        self.watch(0.0, 0.2)
        insurer = self.company()
        insurance.insure(self.state, insurer.agent_id, self.holder, HARVEST, 100.0)
        before = self.balance(self.holder)
        received = insurance.settle(self.record, self.money, HARVEST, 0.25, 3)
        self.assertAlmostEqual(received[self.holder], 25.0)
        self.assertAlmostEqual(self.balance(self.holder) - before, 25.0)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), self.supply)

    def test_a_year_with_no_loss_pays_nothing_and_joins_the_record(self):
        insurer = self.company()
        insurance.insure(self.state, insurer.agent_id, self.holder, HARVEST, 100.0)
        self.assertEqual(insurance.settle(self.record, self.money, HARVEST, 0.0, 1), {})
        self.assertEqual(self.state.hazards[HARVEST].years, 1)

    def test_this_years_loss_is_not_in_the_premium_that_bought_this_years_cover(self):
        self.watch(0.0, 0.0)
        before = insurance.premium_rate(self.state, HARVEST, MARKET_RATE)
        insurance.settle(self.record, self.money, HARVEST, 0.5, 2)
        self.assertAlmostEqual(before, 0.0)
        self.assertGreater(insurance.premium_rate(self.state, HARVEST, MARKET_RATE), before)

    def test_claims_beyond_the_purse_are_paid_in_proportion_and_the_company_fails_and_its_policies_end(self):
        insurer = self.company(30.0)
        insurance.insure(self.state, insurer.agent_id, self.holder, HARVEST, 100.0)
        insurance.insure(self.state, insurer.agent_id, self.other, HARVEST, 300.0)
        received = insurance.settle(self.record, self.money, HARVEST, 0.5, 4)         # claims of 50 and 150 against 30
        self.assertAlmostEqual(received[self.holder], 30.0 * 50.0 / 200.0)
        self.assertAlmostEqual(received[self.other], 30.0 * 150.0 / 200.0)
        self.assertEqual(insurer.failed_year, 4)
        self.assertEqual(self.state.policies, [])
        self.assertAlmostEqual(self.record.book.money_supply(self.money), self.supply)

    def test_a_failed_company_pays_nothing_the_next_year(self):
        insurer = self.company(30.0)
        insurance.insure(self.state, insurer.agent_id, self.holder, HARVEST, 100.0)
        insurance.settle(self.record, self.money, HARVEST, 0.5, 4)
        self.assertEqual(insurance.settle(self.record, self.money, HARVEST, 0.5, 5), {})

    def test_correlated_losses_in_a_row_exhaust_a_small_company_that_one_loss_would_not(self):
        insurer = self.company(120.0)
        insurance.insure(self.state, insurer.agent_id, self.holder, HARVEST, 100.0)
        insurance.settle(self.record, self.money, HARVEST, 0.5, 1)
        self.assertLess(insurer.failed_year, 0)
        insurance.insure(self.state, insurer.agent_id, self.other, HARVEST, 300.0)
        insurance.settle(self.record, self.money, HARVEST, 0.5, 2)
        self.assertEqual(insurer.failed_year, 2)

    def test_what_a_company_holds_beyond_its_capital_and_the_worst_year_goes_back_to_its_founder(self):
        self.watch(0.0, 0.2)
        insurer = self.company(300.0)
        insurance.insure(self.state, insurer.agent_id, self.holder, HARVEST, 100.0)
        self.record.book.transfer(Transfer(self.holder, insurer.agent_id, self.money, 80.0, "premiums"))
        before = self.balance(self.founder)
        paid = insurance.pay_founder(self.record, insurer, self.money, insurance.required_capital(self.state, insurer.agent_id))
        self.assertAlmostEqual(paid, 80.0)
        self.assertGreaterEqual(self.balance(self.founder) - before, 0.0)
        self.assertAlmostEqual(self.balance(insurer.agent_id), 300.0)

    def test_a_company_does_not_pay_its_founder_below_the_capital_the_worst_year_needs(self):
        self.watch(0.0, 0.9)
        insurer = self.company(10.0)
        insurance.insure(self.state, insurer.agent_id, self.holder, HARVEST, 1000.0)
        self.record.book.transfer(Transfer(self.holder, insurer.agent_id, self.money, 50.0, "premiums"))
        required = insurance.required_capital(self.state, insurer.agent_id)
        self.assertAlmostEqual(required, 900.0)
        self.assertEqual(insurance.pay_founder(self.record, insurer, self.money, required), 0.0)


class AMutual(InsuranceFixture):
    def setUp(self):
        super().setUp()
        self.mutual = insurance.found(self.record, self.founder, 0.0, 0, self.money, mutual=True)

    def test_a_mutual_holds_no_capital_and_charges_no_premium_in_advance(self):
        self.watch(0.0, 0.2)
        insurance.insure(self.state, self.mutual.agent_id, self.holder, HARVEST, 100.0)
        self.assertEqual(self.balance(self.mutual.agent_id), 0.0)
        self.assertEqual(insurance.collect_premiums(self.record, self.money, MARKET_RATE), {})

    def test_the_members_pay_the_claims_between_them_in_proportion_to_what_each_insured(self):
        insurance.insure(self.state, self.mutual.agent_id, self.holder, HARVEST, 100.0)
        insurance.insure(self.state, self.mutual.agent_id, self.other, HARVEST, 300.0)
        before = {member: self.balance(member) for member in (self.holder, self.other)}
        received = insurance.settle(self.record, self.money, HARVEST, 0.5, 2)           # claims of 50 and 150
        self.assertAlmostEqual(received[self.holder], 50.0)
        self.assertAlmostEqual(received[self.other], 150.0)
        net_holder = self.balance(self.holder) - before[self.holder]
        net_other = self.balance(self.other) - before[self.other]
        self.assertAlmostEqual(net_holder, 50.0 - 200.0 * 100.0 / 400.0)     # claim less its part of the 200 of claims
        self.assertAlmostEqual(net_other, 150.0 - 200.0 * 300.0 / 400.0)
        self.assertAlmostEqual(self.balance(self.mutual.agent_id), 0.0)
        self.assertAlmostEqual(self.record.book.money_supply(self.money), self.supply)

    def test_members_who_cannot_pay_their_part_shrink_what_the_claimants_receive(self):
        poor = "nobody:without cash"
        insurance.insure(self.state, self.mutual.agent_id, poor, HARVEST, 300.0)
        insurance.insure(self.state, self.mutual.agent_id, self.holder, HARVEST, 100.0)
        received = insurance.settle(self.record, self.money, HARVEST, 0.5, 2)
        self.assertLess(received[self.holder], 50.0)
        self.assertLess(self.mutual.failed_year, 0)               # a mutual has no purse to fail: it pays what its members could

    def test_a_mutual_does_not_pay_a_founder(self):
        self.assertEqual(insurance.pay_founder(self.record, self.mutual, self.money, 0.0), 0.0)


class Saved(InsuranceFixture):
    def test_hazards_insurers_and_policies_survive_the_save(self):
        self.watch(0.0, 0.2)
        insurer = self.company()
        insurance.insure(self.state, insurer.agent_id, self.holder, HARVEST, 100.0)
        self.state.exposure[self.holder] = {HARVEST: 100.0}
        loaded = EconomyRecord.from_record(self.record.to_record())
        self.assertEqual(loaded.capital.to_plain(), self.state.to_plain())
        self.assertEqual(loaded.capital.policies[0].holder, self.holder)


if __name__ == "__main__":
    unittest.main()
