"""The finance module's steps over plain values for the views they read: the year's interest, the insolvency count and what it bleeds,
the debt a default puts into service, the lenders' meeting, a lender's posting and the debt the module reports. The rules they
call are tested where they are (test_credit_freeze_rules, test_affordability_and_credit, test_bondage_workshop_rules)."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.actors.api import SetLenderOffers, SettleLenderInterest
from sim.agents.api import EDGE_SAVERS
from sim.agents.api import edges
from sim.finance.commands import NoteLenderPosting
from sim.finance.constants import (DEBT_BONDAGE_DEFAULT_TERM_YEARS, INSOLVENCY_ARTISAN_FLOOR, INSOLVENCY_YEARS_BEFORE_BLEED)
from sim.finance.state import FinanceSeat
from sim.ledger.api import NoteHolderBooking, SettleHouseholdInterest, SettleWithEdge
from sim.reporting.api import RecordEvent
from sim.tests import finance_host, module_harness


def events(module):
    return [command for command in module_harness.sent(module) if isinstance(command, RecordEvent)]


class ChargeInterest(unittest.TestCase):
    def household(self, capital, arrears=0.0, settle=lambda command: (0.0, 0.0)):
        return finance_host.build(seat=FinanceSeat(interest_arrears=arrears, insolvent_years=1), acting_balance=capital,
                                  answers={SettleHouseholdInterest: settle})

    def test_a_household_in_credit_with_no_arrears_pays_nothing(self):
        module = self.household(100.0, settle=lambda command: self.fail("it was asked to settle"))
        self.assertEqual(module.charge_interest(100), 0.0)
        self.assertIsNone(module.seat.interest_paid)

    def test_what_is_paid_is_added_to_the_interest_paid_so_far(self):
        module = self.household(-500.0, settle=lambda command: (30.0, 20.0))
        module.debt_interest_rate = lambda: 0.06
        self.assertEqual(module.charge_interest(100), 30.0)
        self.assertEqual(module.seat.interest_paid, 20.0)
        module.charge_interest(101)
        self.assertEqual(module.seat.interest_paid, 40.0)

    def test_unpaid_interest_is_said_with_its_facts_in_the_first_years(self):
        module = self.household(-500.0, settle=lambda command: (30.0, 20.0))
        module.debt_interest_rate = lambda: 0.06
        module.charge_interest(100)
        event, = events(module)
        self.assertEqual(event.kind, "arrears_interest")
        self.assertEqual((event.facts["unpaid"], event.facts["rate"]), (10.0, 0.06))

    def test_arrears_alone_keep_the_household_in_the_rule(self):
        module = self.household(100.0, arrears=5.0, settle=lambda command: (3.0, 3.0))
        self.assertEqual(module.charge_interest(100), 3.0)


class JudgeInsolvency(unittest.TestCase):
    def module(self, capital, revenue, years=0, artisans=10.0, scholars=5.0):
        household = SimpleNamespace(capital=capital, artisans=artisans, scholars=scholars, slaves=0, freedmen=0)
        module = finance_host.build(seat=FinanceSeat(insolvent_years=years), household=household, revenue_estimate=revenue)
        module.recurring_living_cost = lambda revenue, upkeep: 0.0
        return module, household

    def test_a_household_in_credit_is_not_insolvent(self):
        module, _household = self.module(10.0, 0.0, years=4)
        module.judge_insolvency()
        self.assertEqual(module.seat.insolvent_years, 0)

    def test_a_year_in_arrears_with_a_surplus_does_not_count(self):
        module, _household = self.module(-10.0, 100.0, years=2)
        module.judge_insolvency()
        self.assertEqual(module.seat.insolvent_years, 0)

    def test_a_year_in_arrears_without_a_surplus_counts(self):
        module, _household = self.module(-10.0, 0.0, years=2)
        module.judge_insolvency()
        self.assertEqual(module.seat.insolvent_years, 3)

    def test_deep_arrears_for_years_bleed_the_staff_down_to_a_floor(self):
        module, household = self.module(-1.0e12, 0.0, years=INSOLVENCY_YEARS_BEFORE_BLEED)
        module.judge_insolvency()
        self.assertLess(household.artisans, 10.0)
        self.assertGreaterEqual(household.artisans, INSOLVENCY_ARTISAN_FLOOR)

    def test_shallow_arrears_bleed_nobody(self):
        module, household = self.module(-1.0, 0.0, years=INSOLVENCY_YEARS_BEFORE_BLEED)
        module.judge_insolvency()
        self.assertEqual((household.artisans, household.scholars), (10.0, 5.0))


class EnterDebtBondage(unittest.TestCase):
    def module(self, civilisation, years_left=0.0):
        module = finance_host.build(seat=FinanceSeat(bondage_years_left=years_left), civilisation=civilisation, acting_balance=-700.0)
        return module

    def test_a_society_with_debt_bondage_puts_the_debtor_into_service_for_the_term(self):
        module = self.module({"debt_bondage": True, "bondage_years": 8.0})
        self.assertTrue(module.enter_debt_bondage(100))
        settled = [(command.edge, command.balance) for command in module_harness.sent(module) if isinstance(command, SettleWithEdge)]
        self.assertEqual((module.seat.bondage_years_left, module.seat.bondage_debt), (8.0, 700.0))
        self.assertEqual(settled, [(edges.EDGE_CREDITORS, 0.0)])
        self.assertEqual([event.kind for event in events(module)], ["debt_bondage"])

    def test_a_society_without_it_does_not(self):
        module = self.module({"debt_bondage": False})
        self.assertFalse(module.enter_debt_bondage(100))
        self.assertEqual((module.seat.bondage_years_left, [c for c in module_harness.sent(module) if isinstance(c, SettleWithEdge)]), (0.0, []))

    def test_a_debtor_already_in_service_is_not_put_in_again(self):
        module = self.module({"debt_bondage": True}, years_left=3.0)
        self.assertFalse(module.enter_debt_bondage(100))
        self.assertEqual(module.seat.bondage_years_left, 3.0)

    def test_the_default_term_stands_when_the_civilisation_names_none(self):
        self.assertEqual(finance_host.build(civilisation={"debt_bondage": True}).debt_bondage_term_years(), DEBT_BONDAGE_DEFAULT_TERM_YEARS)


class LendersMeeting(unittest.TestCase):
    def sent(self, module, kind):
        return [command for command in module_harness.sent(module) if isinstance(command, kind)]

    def test_the_year_shares_the_pools_interest_before_it_fixes_who_offers_what(self):
        world = SimpleNamespace(household_saving=lambda: 3.0)
        government = SimpleNamespace(actor_id="state", money=1000.0, record=SimpleNamespace(need={"army": 400.0}),
                                     cannot_meet_own_need=lambda: False)
        module = finance_host.build(state_treasury=government, actor_world=world)
        module.refresh_lender_offers()
        kinds = [type(command) for command in module_harness.sent(module)]
        self.assertEqual(kinds, [SettleLenderInterest, SetLenderOffers])
        offers = dict(self.sent(module, SetLenderOffers)[0].offers)
        self.assertEqual(offers[EDGE_SAVERS], 30.0)
        self.assertGreater(offers["state"], 0.0)

    def test_a_firm_and_a_purse_lender_offer_what_they_hold_in_purse_and_deposit(self):
        firm, abbey = SimpleNamespace(actor_id="firm:1"), SimpleNamespace(actor_id="abbey")
        module = finance_host.build(cast=SimpleNamespace(actors={}, active_firms=lambda: [firm], purse_lenders=lambda: [abbey]),
                                    cash_and_deposit={"firm:1": 40.0, "abbey": 9.5}.get,
                                    state_treasury=SimpleNamespace(actor_id="state"))
        offers = module.lender_offers({"households": 6.0, "state": 2.0})
        self.assertEqual(offers, {EDGE_SAVERS: 6.0, "state": 2.0, "firm:1": 40.0, "abbey": 9.5})


class LenderPosting(unittest.TestCase):
    def test_a_lender_posting_is_handed_to_the_ledger_to_enter_in_the_lenders_books(self):
        module = finance_host.build()
        module.note_lender_posting(NoteLenderPosting("seat:a", 5.0, "loan"))
        module.note_lender_posting(NoteLenderPosting("abbey", -2.0, "repaid"))
        self.assertEqual(module_harness.sent(module), [NoteHolderBooking("seat:a", 5.0, "loan"), NoteHolderBooking("abbey", -2.0, "repaid")])


class DebtStatus(unittest.TestCase):
    def test_it_reports_every_figure_of_the_seats_debt(self):
        seat = FinanceSeat(credit_frozen_until=110, insolvent_years=2, interest_arrears=4.0, arrears_years=1, bondage_years_left=3.0,
                           bondage_debt=90.0, last_settlement=95, interest_paid=12.0)
        status = finance_host.build(seat=seat).debt_status()
        self.assertEqual(status, {"credit_frozen_until": 110, "insolvent_years": 2, "interest_arrears": 4.0, "arrears_years": 1,
                                  "bondage_years_left": 3.0, "bondage_debt": 90.0, "last_settlement": 95, "interest_paid": 12.0})


if __name__ == "__main__":
    unittest.main()
