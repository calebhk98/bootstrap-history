"""Forces that pull land concentration back: partible inheritance, the cost of managing many tenancies, and a
state's debt relief."""

QUICK_TOPIC = True

import unittest

from sim.agents.policy import CallbackPolicy, IdlePolicy
from sim.agents import policy_land
from sim.economy import debt_relief, titles, titles_inheritance, titles_management
from sim.economy.households_cohort import cohort_id, cohorts_for_tile
from sim.economy.credit_claims import debts_by_borrower
from sim.economy.types import Loan, Transfer
from sim.tests.test_economy_titles import LANDLORD, MONEY, PEASANT, RATE, RENT_PER_HECTARE, TILE, make_world


def concentrate(record, amount):
    """The landlord has taken `amount` of the land from the peasant class, as a foreclosure would."""
    record.titles[TILE][PEASANT] -= amount
    record.titles[TILE][LANDLORD] += amount


class InheritanceTests(unittest.TestCase):
    def test_a_generations_share_of_the_land_above_the_opening_share_passes_to_the_class_that_lost_it(self):
        _setup, record = make_world()
        concentrate(record, 0.05)
        gathered = titles.holding(record, TILE, LANDLORD) - record.cohorts[LANDLORD].ownership_share
        before_peasant = titles.holding(record, TILE, PEASANT)
        moved = titles_inheritance.divide_estates(record, generation_years=10.0, partible_share=1.0)
        self.assertAlmostEqual(moved[TILE], gathered / 10.0)
        self.assertAlmostEqual(titles.holding(record, TILE, PEASANT), before_peasant + gathered / 10.0)
        self.assertAlmostEqual(sum(record.titles[TILE].values()), 1.0)

    def test_inheritance_over_many_generations_returns_holdings_to_the_opening_shares(self):
        _setup, record = make_world()
        concentrate(record, 0.05)
        for _year in range(300):
            titles_inheritance.divide_estates(record, generation_years=10.0, partible_share=1.0)
        for cohort in record.cohorts.values():
            self.assertAlmostEqual(titles.holding(record, TILE, cohort.agent_id), cohort.ownership_share, places=3)

    def test_an_estate_that_does_not_divide_stays_whole(self):
        _setup, record = make_world()
        concentrate(record, 0.05)
        before = dict(record.titles[TILE])
        self.assertEqual(titles_inheritance.divide_estates(record, generation_years=10.0, partible_share=0.0), {})
        self.assertEqual(record.titles[TILE], before)

    def test_pledged_land_does_not_pass_to_heirs(self):
        _setup, record = make_world()
        concentrate(record, 0.05)
        record.loans.append(Loan("loan:1", "lender", LANDLORD, MONEY, 10.0, 0.05, 1.0, 0.0, collateral_tile=TILE,
                                 collateral_share=titles.holding(record, TILE, LANDLORD)))
        self.assertEqual(titles_inheritance.divide_estates(record, generation_years=10.0, partible_share=1.0), {})

    def test_a_tenant_who_inherits_from_its_lessor_holds_that_land_outright(self):
        _setup, record = make_world()
        concentrate(record, 0.05)
        record.tenancies = {TILE: [{"tenant": PEASANT, "lessor": LANDLORD, "share": 0.05, "arrears": 0.0}]}
        titles_inheritance.divide_estates(record, generation_years=10.0, partible_share=1.0)
        self.assertLess(titles.tenant_share(record, TILE, PEASANT), 0.05)
        for _year in range(300):
            titles_inheritance.divide_estates(record, generation_years=10.0, partible_share=1.0)
        self.assertLess(titles.tenant_share(record, TILE, PEASANT), 1e-6)


class ManagementCostTests(unittest.TestCase):
    def lessor_world(self, tenancies):
        setup, record = make_world()
        record.tenancies = {}
        for index in range(tenancies):
            tile = "tile%d" % index
            for cohort in cohorts_for_tile(tile, 300.0, 0.5, 0.4, class_count=3):
                record.cohorts[cohort.agent_id] = cohort
            tenant = cohort_id(tile, 1)
            record.titles[tile] = {LANDLORD: 0.1}
            record.land_rent[tile] = RENT_PER_HECTARE
            record.tenancies[tile] = [{"tenant": tenant, "lessor": LANDLORD, "share": 0.1, "arrears": 0.0}]
            record.book.transfer(Transfer("edge:harvest", tenant, MONEY, 1000.0, "harvest"))
        arable = {"tile%d" % index: 100.0 for index in range(tenancies)}
        return record, arable

    def test_cost_share_rises_with_the_number_of_tenancies_and_a_lone_tenancy_is_free(self):
        self.assertEqual(titles_management.cost_share(1), 0.0)
        self.assertLess(titles_management.cost_share(5), titles_management.cost_share(20))
        self.assertEqual(titles_management.cost_share(10 ** 6), 1.0)

    def test_a_lessor_with_many_tenancies_keeps_a_smaller_share_of_each_rent(self):
        few, arable_few = self.lessor_world(2)
        many, arable_many = self.lessor_world(20)
        kept_few = sum(p.amount for p in titles.settle_tenancies(few, MONEY, arable_few) if p.payee == LANDLORD) / 2
        kept_many = sum(p.amount for p in titles.settle_tenancies(many, MONEY, arable_many) if p.payee == LANDLORD) / 20
        self.assertLess(kept_many, kept_few)

    def test_the_cost_is_paid_to_stewards_not_lost(self):
        record, arable = self.lessor_world(20)
        payments = titles.settle_tenancies(record, MONEY, arable)
        stewards = [p for p in payments if p.purpose == "steward_pay"]
        self.assertGreater(sum(p.amount for p in stewards), 0.0)
        self.assertAlmostEqual(sum(p.amount for p in payments), 20 * 0.1 * 100.0 * RENT_PER_HECTARE)

    def test_a_tenancy_whose_cost_eats_all_its_rent_is_given_up_to_the_tenant(self):
        record, arable = self.lessor_world(5)
        titles.settle_tenancies(record, MONEY, arable, management_cost_per_extra_tenancy=0.5)
        self.assertEqual(record.tenancies, {})
        self.assertAlmostEqual(titles.holding(record, "tile0", cohort_id("tile0", 1)), 0.1)
        self.assertEqual(titles.holding(record, "tile0", LANDLORD), 0.0)


class DebtReliefTests(unittest.TestCase):
    def indebted_world(self):
        _setup, record = make_world()
        record.loans.append(Loan("loan:2", "lender", PEASANT, MONEY, 80.0, 0.05, 2.0, 0.0))
        record.loans.append(Loan("loan:3", "lender", "household:elsewhere:0", MONEY, 50.0, 0.05, 2.0, 0.0))
        record.tenancies = {TILE: [{"tenant": PEASANT, "lessor": LANDLORD, "share": 0.1, "arrears": 12.0}]}
        return record

    def test_relief_cancels_the_tiles_household_debts_and_the_lender_books_the_loss(self):
        record = self.indebted_world()
        written_off = debt_relief.forgive(record, [TILE])
        self.assertEqual(written_off["principal"], 80.0)
        self.assertEqual(debts_by_borrower(record.loans, MONEY).get(PEASANT, 0.0), 0.0)
        self.assertEqual(record.credit_losses["lender"], 80.0)

    def test_relief_leaves_other_tiles_debts_and_every_title_alone(self):
        record = self.indebted_world()
        titles_before = {tile: dict(held) for tile, held in record.titles.items()}
        debt_relief.forgive(record, [TILE])
        self.assertEqual([loan.borrower for loan in record.loans], ["household:elsewhere:0"])
        self.assertEqual(record.titles, titles_before)

    def test_relief_forgives_rent_arrears_so_a_tenant_is_not_evicted_for_them(self):
        record = self.indebted_world()
        self.assertEqual(debt_relief.forgive(record, [TILE])["rent_arrears"], 12.0)
        self.assertEqual(record.tenancies[TILE][0]["arrears"], 0.0)

    def test_no_tiles_means_no_relief(self):
        record = self.indebted_world()
        debt_relief.forgive(record, [])
        self.assertEqual(len(record.loans), 2)

    def test_the_indebted_tiles_are_those_where_a_household_owes(self):
        self.assertEqual(debt_relief.indebted_tiles(self.indebted_world()), [TILE])


class StateChoiceTests(unittest.TestCase):
    class State:
        decision_policy = None

    def test_a_state_with_the_default_policy_offers_relief_to_nobody(self):
        self.assertEqual(policy_land.debt_relief_tiles(self.State(), ["a", "b"]), [])

    def test_a_state_whose_policy_chooses_relief_gets_it_for_the_tiles_it_names(self):
        state = self.State()
        state.decision_policy = CallbackPolicy(lambda actor, decision: ["b"] if decision.kind == "debt_relief" else [])
        self.assertEqual(policy_land.debt_relief_tiles(state, ["a", "b"]), ["b"])

    def test_an_idle_policy_chooses_nothing(self):
        state = self.State()
        state.decision_policy = IdlePolicy()
        self.assertEqual(policy_land.debt_relief_tiles(state, ["a"]), [])


if __name__ == "__main__":
    unittest.main()
