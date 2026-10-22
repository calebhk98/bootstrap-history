"""Complaints 605 and 607: household saving finds a use. A household counts what it owns of the firms among the
wealth it wants to hold, so it does not also keep that wealth as idle cash; more of its income reaches a spender
(goods, or a producer's loan). Values are read from the economy's records, not from text.

Rules (Complaint 640): `EquityTests` calls `equity.firm_net_worth`, `equity_of` and `goods_orders` on built inputs.
The old paired whole-run comparison (with and without the equity read, lent share at least double) is deleted: the
fixture run no longer separates the two, and its rule is the one `goods_orders` test above. One baseline validation
remains (`BaselineValidationSavingReachesAProducerTests`)."""
import dataclasses
import unittest

from sim.economy import api as economy_api, credit_claims, equity
from sim.economy.credit_view import equity_of
from sim.economy.economy import Economy
from sim.economy.households_orders import goods_orders
from sim.economy.households_basket import need_prices
from sim.economy.year_ledger import YearLedger
from sim.tests import economy_fixture as fixture

YEARS = 40
WARM_UP_YEARS = 5
SURPLUS_FACTOR = 20.0


def plant_setup():
    """The fixture with plant on the farm and the mine, so a producer can be a place to put savings."""
    base = fixture.small_setup()
    recipes = dict(base.recipes)
    recipes[fixture.FARM] = dataclasses.replace(
        recipes[fixture.FARM], plant_goods={fixture.METAL: 0.4}, plant_labour_hours={fixture.LABOURER: 40.0},
        plant_life_years=20.0)
    recipes[fixture.MINE] = dataclasses.replace(
        recipes[fixture.MINE], plant_goods={fixture.METAL: 0.1}, plant_labour_hours={fixture.MINER: 20.0},
        plant_life_years=20.0)
    return dataclasses.replace(base, recipes=recipes)


class _Owning:
    """A view that reads like the real one but says every agent owns `worth` of the firms."""

    def __init__(self, view, worth):
        self._view = view
        self._worth = worth

    def __getattr__(self, name):
        return getattr(self._view, name)

    def equity(self, agent):
        return self._worth


class EquityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = plant_setup()
        cls.economy = Economy(cls.setup)
        cls.economy.step(fixture.quiet_year(cls.setup))

    def test_the_owners_share_the_net_worth_of_their_firms_by_ownership_share(self):
        record, view = self.economy.record, self.economy.view()
        money = self.setup.currency_id
        debts = credit_claims.debts_by_borrower(record.loans, money)
        total = 0.0
        for producer_id, producer in record.producers.items():
            recipe = self.setup.recipes[producer.recipe_id]
            total += equity.firm_net_worth(producer, recipe, record.book.balance(producer_id, money),
                                           debts.get(producer_id, 0.0), view)
        held = {cohort_id: equity_of(view, cohort_id) for cohort_id in record.cohorts}
        self.assertAlmostEqual(sum(held.values()), total, delta=1e-6 * total)
        self.assertGreater(total, 0.0)
        tile = next(iter(self.setup.tiles))
        owners = [cohort for cohort in record.cohorts.values() if cohort.tile == tile]
        ratios = [held[cohort.agent_id] / cohort.ownership_share for cohort in owners]
        for ratio in ratios:
            self.assertAlmostEqual(ratio, ratios[0], delta=1e-6 * ratios[0])

    def test_a_cohort_that_owns_firms_spends_more_than_one_that_owns_none(self):
        record, view = self.economy.record, self.economy.view()
        setup = self.setup
        spent = {}
        income = SURPLUS_FACTOR * sum(cohort.last_year_income for cohort in record.cohorts.values())
        for label, seen in (("owns", _Owning(view, 10.0 * income)), ("none", _Owning(view, 0.0))):
            total = 0.0
            for cohort in record.cohorts.values():
                cohort = dataclasses.replace(cohort, expected_spending=0.0)    # no habit of spending to hold it up
                income = SURPLUS_FACTOR * cohort.last_year_income     # an income well above the floors
                cash = income
                orders = goods_orders(cohort, seen, cash, income, setup.basket_for(cohort.tile), setup.specs,
                                      need_prices(setup.basket_for(cohort.tile), seen, cohort.tile),
                                      smooth_rise=False)
                total += sum(bid.budget for bid in orders.bids)
            spent[label] = total
        self.assertGreater(spent["owns"], spent["none"])

    def test_a_cohort_that_owns_firms_keeps_less_idle_cash_to_offer_for_loan(self):
        record, view = self.economy.record, self.economy.view()
        setup = self.setup
        offered = {}
        for label, worth in (("owns", 10.0 * SURPLUS_FACTOR * sum(c.last_year_income for c in record.cohorts.values())),
                             ("none", 0.0)):
            seen = _Owning(view, worth)
            total = 0.0
            for cohort in record.cohorts.values():
                cohort = dataclasses.replace(cohort, expected_spending=0.0)
                income = SURPLUS_FACTOR * cohort.last_year_income
                orders = goods_orders(cohort, seen, income, income, setup.basket_for(cohort.tile), setup.specs,
                                      need_prices(setup.basket_for(cohort.tile), seen, cohort.tile),
                                      smooth_rise=False)
                total += sum(offer.amount for offer in orders.funds_offers)
            offered[label] = total
        self.assertGreater(offered["none"], 0.0)
        self.assertLess(offered["owns"], offered["none"])

    def test_working_capital_struck_ahead_of_the_year_leaves_no_plant_to_wait_for(self):
        economy = Economy(self.setup)
        economy.record.expansion_runs = {"producer:x": 0.0}
        economy.record.loan_requests = []
        economy._lend([], economy.view(), {}, YearLedger())
        self.assertEqual(economy.record.expansion_runs, {})


def _lent_share(years=YEARS, warm_up=WARM_UP_YEARS):
    """Lent over offered, summed over the warmed-up years of the plant fixture's quiet run."""
    setup = plant_setup()
    economy = Economy(setup)
    economy_api.begin_spin_up(economy)
    lent = offered = 0.0
    for year in range(years):
        economy.step(fixture.quiet_year(setup))
        if year >= warm_up:
            lent += sum(economy.record.lent_by_borrower.values())
            offered += economy.record.funds_offered
    return lent, offered


class BaselineValidationSavingReachesAProducerTests(unittest.TestCase):
    """Baseline validation (CLAUDE.md 4.2, Complaint 640), slow only: in a quiet economy with plant on its farms and
    mines, some of the savings on offer are lent to producers. It reads the whole run, so a failure names no rule;
    the rules (equity counts as wealth held, so less cash is offered idle) are held by EquityTests.
    The households have a surplus to save: the settled opening leaves none (Complaint 607), and the question here is
    whether a surplus finds a use."""

    def setUp(self):
        fixture.households_with_a_surplus(self)

    def test_validation_some_savings_on_offer_are_lent_to_producers(self):
        lent, offered = _lent_share()
        self.assertGreater(offered, 0.0)
        self.assertGreater(lent / offered, 0.0, "no savings reached a producer in %d quiet years" % YEARS)


if __name__ == "__main__":
    unittest.main()
