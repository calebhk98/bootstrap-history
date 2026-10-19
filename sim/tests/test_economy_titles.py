"""Land titles: seeded from ownership, pledged for loans, passed by default to a lender whose borrower stays as
tenant, abandoned when the tenant falls a year behind, valued as capitalised rent, and saved with the record."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import credit, credit_claims, lending, ownership, titles, titles_value
from sim.economy.accounts import Book
from sim.economy.households_cohort import cohort_id, cohorts_for_tile
from sim.economy.households_credit import subsistence_request
from sim.economy.market_memory import MarketMemory
from sim.economy.record import EconomyRecord
from sim.economy.types import CurrencySpec, FundsOffer, TileSpec, Transfer

MONEY = "coin"
TILE = "t"
PEASANT, LANDLORD = cohort_id(TILE, 0), cohort_id(TILE, 2)
RENT_PER_HECTARE = 2.0
RATE = 0.05
FLOOR_COST = 100.0                 # what the peasant household must spend a year
NORMAL_INCOME = 300.0


def make_world():
    tile = TileSpec(TILE, 40.0, 10.0, 1.0, False, (), 1.0, 1.0)     # one square kilometre: a hundred hectares
    setup = types.SimpleNamespace(currency_id=MONEY, tiles={TILE: tile}, opening_rate=RATE)
    record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec(MONEY, "fiat", None, 0.0, None))
    for cohort in cohorts_for_tile(TILE, 300.0, 0.5, 0.4, class_count=3):
        record.cohorts[cohort.agent_id] = cohort
    peasant = record.cohorts[PEASANT]
    record.cohorts[PEASANT] = type(peasant)(**{**vars(peasant), "last_year_income": NORMAL_INCOME})
    titles.seed(record)
    record.land_rent = {TILE: RENT_PER_HECTARE}
    record.book.transfer(Transfer("edge:legacy", LANDLORD, MONEY, 100000.0, "opening"))
    return setup, record


def one_year(setup, record, year, income):
    """The peasant household borrows against its plot for what its cash does not cover of its floor, spends the
    floor, earns `income`, and then the year's loans are serviced."""
    cohort = record.cohorts[PEASANT]
    cash = record.book.balance(PEASANT, MONEY)
    debts = credit_claims.debts_by_borrower(record.loans, MONEY)
    asked = subsistence_request(cohort, FLOOR_COST - cash, MONEY, RATE, debts.get(PEASANT, 0.0))
    if asked is not None:
        asked = lending._pledging_title(setup, record, cohort, asked, RATE)
        loans, rate, _unmet = credit.clear([asked], [FundsOffer(LANDLORD, MONEY, 50000.0, RATE)], MONEY, RATE,
                                           debts, credit_claims.arrears_history(record.loans, record.remembered_defaults),
                                           year=year)
        record.book.transfer_many(credit.disbursements(loans))
        record.loans.extend(loans)
    spend = min(FLOOR_COST, record.book.balance(PEASANT, MONEY))
    record.book.transfer(Transfer(PEASANT, "edge:market", MONEY, spend, "spending"))
    record.book.transfer(Transfer("edge:harvest", PEASANT, MONEY, income, "harvest"))
    lending.service(record, MONEY, year)


def years(setup, record, count, income):
    for year in range(count):
        one_year(setup, record, year, income)


class SeedingTests(unittest.TestCase):
    def test_titles_start_as_the_cohorts_ownership_shares(self):
        _setup, record = make_world()
        self.assertAlmostEqual(sum(record.titles[TILE].values()), 1.0)
        for cohort in record.cohorts.values():
            self.assertAlmostEqual(titles.holding(record, TILE, cohort.agent_id), cohort.ownership_share)

    def test_rent_to_the_owner_is_split_by_title_not_by_ownership_once_a_title_moves(self):
        _setup, record = make_world()
        by_share = {payment.payee: payment.amount for payment in
                    ownership.spread(record, [Transfer("producer:a", LANDLORD, MONEY, 100.0, "rent")])}
        record.titles[TILE][LANDLORD] += record.titles[TILE].pop(PEASANT)
        moved = {payment.payee: payment.amount for payment in
                 ownership.spread(record, [Transfer("producer:a", LANDLORD, MONEY, 100.0, "rent")])}
        self.assertNotIn(PEASANT, moved)
        self.assertAlmostEqual(moved[LANDLORD], by_share[LANDLORD] + by_share[PEASANT])


class OpeningTests(unittest.TestCase):
    def test_an_opened_economy_seeds_titles_from_ownership_shares(self):
        from sim.tests import economy_fixture
        record = economy_fixture.Economy(economy_fixture.small_setup()).record
        self.assertEqual(set(record.titles), {cohort.tile for cohort in record.cohorts.values()})
        for cohort in record.cohorts.values():
            self.assertAlmostEqual(record.titles[cohort.tile][cohort.agent_id], cohort.ownership_share)
        self.assertEqual(record.tenancies, {})


class ValueTests(unittest.TestCase):
    def test_a_title_is_worth_its_capitalised_rent_and_moves_with_the_title(self):
        setup, record = make_world()
        share = titles.holding(record, TILE, PEASANT)
        worth = titles_value.title_wealth(setup.tiles, record, PEASANT, RATE)
        self.assertAlmostEqual(worth, share * 100.0 * RENT_PER_HECTARE / RATE)
        record.titles[TILE][LANDLORD] += record.titles[TILE].pop(PEASANT)
        self.assertEqual(titles_value.title_wealth(setup.tiles, record, PEASANT, RATE), 0.0)
        self.assertGreater(titles_value.title_wealth(setup.tiles, record, LANDLORD, RATE), worth)


class HarvestAndDefaultTests(unittest.TestCase):
    def test_a_good_run_leaves_titles_where_they_were(self):
        setup, record = make_world()
        before = dict(record.titles[TILE])
        years(setup, record, 8, income=NORMAL_INCOME)
        self.assertEqual(record.titles[TILE], before)
        self.assertEqual(record.tenancies, {})

    def test_bad_harvests_pass_the_borrowers_title_to_the_lender_and_the_family_stays_as_tenant(self):
        setup, record = make_world()
        before = dict(record.titles[TILE])
        years(setup, record, 8, income=0.1 * FLOOR_COST)
        self.assertLess(titles.holding(record, TILE, PEASANT), before[PEASANT])
        self.assertGreater(titles.holding(record, TILE, LANDLORD), before[LANDLORD])
        self.assertAlmostEqual(sum(record.titles[TILE].values()), 1.0)
        self.assertGreater(titles.tenant_share(record, TILE, PEASANT), 0.0)
        self.assertAlmostEqual(titles.tenant_share(record, TILE, PEASANT),
                               titles.holding(record, TILE, LANDLORD) - before[LANDLORD])

    def test_the_defaulted_family_pays_the_lender_rent_on_the_land_it_still_works(self):
        setup, record = make_world()
        years(setup, record, 8, income=0.1 * FLOOR_COST)
        record.book.transfer(Transfer("edge:harvest", PEASANT, MONEY, 1000.0, "harvest"))
        landlord_cash = record.book.balance(LANDLORD, MONEY)
        payments = titles.settle_tenancies(record, MONEY, {TILE: 100.0})
        record.book.transfer_many(payments)
        self.assertAlmostEqual(record.book.balance(LANDLORD, MONEY) - landlord_cash,
                               titles.tenant_share(record, TILE, PEASANT) * 100.0 * RENT_PER_HECTARE)

    def test_a_pledge_cheapens_the_loan(self):
        setup, record = make_world()
        cohort = record.cohorts[PEASANT]
        bare = subsistence_request(cohort, 50.0, MONEY, RATE, 0.0)
        pledged = lending._pledging_title(setup, record, cohort, bare, RATE)
        self.assertGreater(pledged.collateral_value, 0.0)
        offers = [FundsOffer(LANDLORD, MONEY, 5000.0, RATE)]
        plain_loan = credit.clear([bare], offers, MONEY, RATE, {})[0][0]
        secured = credit.clear([pledged], offers, MONEY, RATE, {})[0][0]
        self.assertLess(secured.rate, plain_loan.rate)
        self.assertEqual((secured.collateral_tile, secured.collateral_share > 0.0), (TILE, True))

    def test_a_lender_that_takes_the_land_loses_less_by_default(self):
        setup, record = make_world()
        years(setup, record, 8, income=0.1 * FLOOR_COST)
        self.assertGreater(titles.tenant_share(record, TILE, PEASANT), 0.0)
        covered = record.credit_losses.get(LANDLORD, 0.0)
        setup2, bare = make_world()
        bare.land_rent = {}                                    # land that earns nothing is no collateral
        years(setup2, bare, 8, income=0.1 * FLOOR_COST)
        self.assertLess(covered, bare.credit_losses[LANDLORD])


class TenancyTests(unittest.TestCase):
    def tenant_world(self, share=0.1):
        setup, record = make_world()
        record.titles[TILE][PEASANT] -= share
        record.titles[TILE][LANDLORD] += share
        record.tenancies = {TILE: [{"tenant": PEASANT, "lessor": LANDLORD, "share": share, "arrears": 0.0}]}
        return setup, record

    def test_a_tenant_pays_its_lessor_the_rent_on_the_land_it_works(self):
        setup, record = self.tenant_world(0.1)
        record.book.transfer(Transfer("edge:harvest", PEASANT, MONEY, 1000.0, "harvest"))
        payments = titles.settle_tenancies(record, MONEY, {TILE: 100.0})
        self.assertEqual([(payment.payer, payment.payee, payment.purpose) for payment in payments],
                         [(PEASANT, LANDLORD, "tenant_rent")])
        self.assertAlmostEqual(payments[0].amount, 0.1 * 100.0 * RENT_PER_HECTARE)
        self.assertEqual(record.tenancies[TILE][0]["arrears"], 0.0)

    def test_rent_it_cannot_pay_builds_arrears_and_a_year_behind_abandons_the_land(self):
        setup, record = self.tenant_world(0.1)
        landlord_before = titles.holding(record, TILE, LANDLORD)
        titles.settle_tenancies(record, MONEY, {TILE: 100.0})            # first short year: arrears, still a tenant
        self.assertEqual(titles.tenant_share(record, TILE, PEASANT), 0.1)
        self.assertGreater(record.tenancies[TILE][0]["arrears"], 0.0)
        titles.settle_tenancies(record, MONEY, {TILE: 100.0})            # second: more than a year's rent behind
        self.assertEqual(record.tenancies, {})
        self.assertAlmostEqual(titles.holding(record, TILE, LANDLORD), landlord_before - 0.1)
        self.assertAlmostEqual(sum(record.titles[TILE].values()), 0.9)    # the land has no holder now
        paid = ownership.spread(record, [Transfer("producer:a", LANDLORD, MONEY, 90.0, "rent")])
        self.assertAlmostEqual(sum(payment.amount for payment in paid), 90.0)   # rent still reaches the holders


class SaveTests(unittest.TestCase):
    def test_titles_tenancies_and_pledges_survive_a_save_and_load(self):
        setup, record = make_world()
        years(setup, record, 8, income=0.1 * FLOOR_COST)
        loaded = EconomyRecord.from_record(record.to_record())
        self.assertEqual(loaded.titles, record.titles)
        self.assertEqual(loaded.tenancies, record.tenancies)
        self.assertEqual([(loan.collateral_tile, loan.collateral_share) for loan in loaded.loans],
                         [(loan.collateral_tile, loan.collateral_share) for loan in record.loans])
        self.assertGreater(len(loaded.tenancies[TILE]), 0)


if __name__ == "__main__":
    unittest.main()
