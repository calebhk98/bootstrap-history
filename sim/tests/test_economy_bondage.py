"""Debt bondage for household cohorts: a default by a household with no land left binds it to its creditor for a
term, and the creditor takes the owed share of the hours' product (the wages) until the debt is worked off."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import bondage, credit, credit_claims, lending, titles
from sim.economy.credit import Default
from sim.economy.types import FundsOffer, LoanRequest, Transfer
from sim.tests.test_economy_titles import FLOOR_COST, LANDLORD, MONEY, PEASANT, RATE, TILE, make_world, years

TERM = 10.0


def landless_default(record, loss=60.0):
    record.titles[TILE][LANDLORD] += record.titles[TILE].pop(PEASANT)
    return Default("loan:1", LANDLORD, PEASANT, MONEY, loss)


class EntryTests(unittest.TestCase):
    def test_a_landless_household_in_default_is_bound_to_its_creditor_for_the_debt_left(self):
        _setup, record = make_world()
        entered = bondage.enter(record, [landless_default(record)], TERM)
        self.assertEqual(entered, [PEASANT])
        self.assertEqual(record.bondage[PEASANT], {"creditor": LANDLORD, "debt": 60.0, "years_left": TERM})

    def test_a_household_that_still_holds_land_is_not_bound(self):
        _setup, record = make_world()
        default = Default("loan:1", LANDLORD, PEASANT, MONEY, 60.0)
        self.assertEqual(bondage.enter(record, [default], TERM), [])
        self.assertEqual(record.bondage, {})

    def test_a_society_without_debt_bondage_binds_nobody(self):
        _setup, record = make_world()
        self.assertEqual(bondage.enter(record, [landless_default(record)], 0.0), [])

    def test_a_further_default_adds_to_the_debt_it_does_not_restart_the_term(self):
        _setup, record = make_world()
        bondage.enter(record, [landless_default(record)], TERM)
        record.bondage[PEASANT]["years_left"] = 4.0
        bondage.enter(record, [Default("loan:2", LANDLORD, PEASANT, MONEY, 10.0)], TERM)
        self.assertEqual(record.bondage[PEASANT]["debt"], 70.0)
        self.assertEqual(record.bondage[PEASANT]["years_left"], 4.0)

    def test_a_firm_or_other_borrower_is_not_bound(self):
        _setup, record = make_world()
        self.assertEqual(bondage.enter(record, [Default("loan:1", LANDLORD, "producer:a", MONEY, 60.0)], TERM), [])


class ServiceTests(unittest.TestCase):
    def bonded_world(self, debt=60.0, cash=1000.0):
        _setup, record = make_world()
        bondage.enter(record, [landless_default(record, debt)], TERM)
        record.book.transfer(Transfer("edge:harvest", PEASANT, MONEY, cash, "harvest"))
        record.credit_losses[LANDLORD] = debt
        return record

    def test_the_creditor_takes_the_owed_share_of_the_years_wages_off_the_debt(self):
        record = self.bonded_world()
        payments = bondage.service(record, MONEY, {PEASANT: 40.0})
        self.assertEqual([(p.payer, p.payee, p.purpose) for p in payments], [(PEASANT, LANDLORD, "bonded_labour")])
        self.assertAlmostEqual(payments[0].amount, bondage.BONDED_HOURS_OWED_SHARE * 40.0)
        self.assertAlmostEqual(record.bondage[PEASANT]["debt"], 60.0 - payments[0].amount)
        self.assertAlmostEqual(record.credit_losses[LANDLORD], 60.0 - payments[0].amount)
        self.assertEqual(record.bondage[PEASANT]["years_left"], TERM - 1.0)

    def test_it_takes_no_more_than_the_household_holds(self):
        record = self.bonded_world(cash=5.0)
        payments = bondage.service(record, MONEY, {PEASANT: 400.0})
        self.assertAlmostEqual(payments[0].amount, 5.0)

    def test_the_bond_ends_when_the_debt_is_worked_off(self):
        record = self.bonded_world(debt=20.0)
        bondage.service(record, MONEY, {PEASANT: 400.0})
        self.assertEqual(record.bondage, {})

    def test_the_bond_ends_when_the_term_is_served_and_the_loss_stands(self):
        record = self.bonded_world(debt=1000.0, cash=0.0)
        for _year in range(int(TERM)):
            bondage.service(record, MONEY, {PEASANT: 0.0})
        self.assertEqual(record.bondage, {})
        self.assertEqual(record.credit_losses[LANDLORD], 1000.0)

    def test_a_household_earning_nothing_pays_nothing(self):
        record = self.bonded_world()
        self.assertEqual(bondage.service(record, MONEY, {}), [])


class DefaultFlowTests(unittest.TestCase):
    def test_a_household_whose_whole_plot_is_taken_and_still_owes_is_bound_by_the_lenders_service(self):
        setup, record = make_world()
        lent = credit.clear([credit_request(record)], [FundsOffer(LANDLORD, MONEY, 50000.0, RATE)], MONEY, RATE, {})[0]
        record.loans.extend(lent)
        record.loans = [loan.__class__(**{**vars(loan), "collateral_value": 1.0}) for loan in record.loans]   # land worth little
        for _year in range(1, 8):
            lending.service(record, MONEY, _year, bondage_years=TERM)
            if record.bondage:
                break
        self.assertIn(PEASANT, record.bondage)
        self.assertEqual(record.bondage[PEASANT]["creditor"], LANDLORD)


def credit_request(record):
    return LoanRequest(PEASANT, MONEY, 80.0, 0.3, 2.0, 1.0, "subsistence",
                       collateral_tile=TILE, collateral_share=titles.holding(record, TILE, PEASANT))


class SaveTests(unittest.TestCase):
    def test_a_bond_survives_a_save_and_load(self):
        from sim.economy.record import EconomyRecord
        _setup, record = make_world()
        bondage.enter(record, [landless_default(record)], TERM)
        self.assertEqual(EconomyRecord.from_record(record.to_record()).bondage, record.bondage)


class OneRuleTests(unittest.TestCase):
    def test_the_founders_term_and_the_cohorts_come_from_one_rule(self):
        from sim.finance.constants import DEBT_BONDAGE_DEFAULT_TERM_YEARS
        from sim.tests import finance_host

        def term(civ):
            return finance_host.build(civilisation=civ).debt_bondage_term_years()
        self.assertEqual(term({"debt_bondage": True, "bondage_years": 7.0}), 7.0)
        self.assertEqual(term({"debt_bondage": True}), DEBT_BONDAGE_DEFAULT_TERM_YEARS)
        self.assertEqual(term({"debt_bondage": False, "bondage_years": 7.0}), 0.0)


if __name__ == "__main__":
    unittest.main()
