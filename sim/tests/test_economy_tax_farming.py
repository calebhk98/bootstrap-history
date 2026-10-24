"""Tax farming: the state lets a money form for a year; the best bidder pays up front and collects from the base."""

QUICK_TOPIC = True

import types
import unittest

from sim.agents import policy_land
from sim.agents.policy import CallbackPolicy
from sim.economy import tax_farming
from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory
from sim.economy.record import EconomyRecord
from sim.economy.taxes import TaxForm
from sim.economy.types import CurrencySpec, Transfer

MONEY = "coin"
STATE = "state:test"
POLL = TaxForm("poll", "adult_labour_years", 0.05)


def bidding_record(base=1000.0, state_take=40.0, cash=None):
    record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec(MONEY, "fiat", None, 0.0, None))
    record.tax_history = {"poll": {"base": base, "state_take": state_take}}
    for agent, amount in (cash or {"rich": 500.0, "poor": 5.0}).items():
        record.book.transfer(Transfer("edge:legacy", agent, MONEY, amount, "opening"))
    return record


def setup_with(_record):
    return types.SimpleNamespace(tax_forms=(POLL,), state_agent=STATE, currency_id=MONEY)


class BidTests(unittest.TestCase):
    def test_a_bid_is_the_expected_take_discounted_a_year_and_no_more_than_the_bidders_cash(self):
        record = bidding_record()
        offers = tax_farming.bids(record, POLL, 0.1, STATE, MONEY)
        self.assertEqual([agent for _price, _cash, agent in offers], ["rich", "poor"])
        self.assertAlmostEqual(offers[0][0], 0.05 * 1000.0 * tax_farming.TAX_FARMER_REACH / 1.1)
        self.assertEqual(offers[1][0], 5.0)

    def test_nobody_bids_without_a_year_of_history(self):
        record = bidding_record()
        record.tax_history = {}
        self.assertEqual(tax_farming.bids(record, POLL, 0.1, STATE, MONEY), [])

    def test_the_best_bid_wins_and_pays_the_state_at_once(self):
        record = bidding_record()
        leases = tax_farming.run_auctions(setup_with(record), record, ["poll"], 0.1)
        self.assertEqual(leases["poll"]["farmer"], "rich")
        self.assertAlmostEqual(record.book.balance(STATE, MONEY), leases["poll"]["price"])
        self.assertAlmostEqual(record.book.balance("rich", MONEY), 500.0 - leases["poll"]["price"])

    def test_the_state_refuses_a_bid_under_what_it_expects_to_collect_itself(self):
        record = bidding_record(state_take=400.0)
        self.assertEqual(tax_farming.run_auctions(setup_with(record), record, ["poll"], 0.1), {})
        self.assertEqual(record.book.balance(STATE, MONEY), 0.0)

    def test_a_form_not_named_is_not_let(self):
        record = bidding_record()
        self.assertEqual(tax_farming.run_auctions(setup_with(record), record, [], 0.1), {})

    def test_a_bidder_short_of_cash_cannot_win_a_lease_it_cannot_pay_for(self):
        record = bidding_record(cash={"poor": 5.0})
        self.assertEqual(tax_farming.run_auctions(setup_with(record), record, ["poll"], 0.1), {})


class RememberYearTests(unittest.TestCase):
    def assessment(self, form, base, collected):
        return types.SimpleNamespace(form=form, base_value=base, collected_value=collected)

    def test_a_year_of_tax_leaves_the_forms_base_and_the_states_take_in_the_record(self):
        record = types.SimpleNamespace(tax_history={})
        tax_farming.remember_year(record, [self.assessment("poll", 1000.0, 40.0)], (), 0.5)
        self.assertEqual(record.tax_history, {"poll": {"base": 1000.0, "state_take": 40.0}})

    def test_a_farmed_forms_take_is_scaled_from_the_farmers_reach_back_to_the_states(self):
        record = types.SimpleNamespace(tax_history={})
        tax_farming.remember_year(record, [self.assessment("poll", 1000.0, 90.0)], ("poll",), 0.5, reach=0.9)
        self.assertAlmostEqual(record.tax_history["poll"]["state_take"], 90.0 * 0.5 / 0.9)


class StateChoiceTests(unittest.TestCase):
    class State:
        decision_policy = None

    def test_a_state_with_the_default_policy_farms_nothing(self):
        self.assertEqual(policy_land.farmed_forms(self.State(), ["poll"]), [])

    def test_a_state_whose_policy_chooses_it_farms_the_form_it_names(self):
        state = self.State()
        state.decision_policy = CallbackPolicy(lambda actor, decision: ["poll"] if decision.kind == "tax_farm" else [])
        self.assertEqual(policy_land.farmed_forms(state, ["poll", "customs"]), ["poll"])


if __name__ == "__main__":
    unittest.main()
