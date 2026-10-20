"""Complaints 605 and 607: household saving finds a use. A household counts what it owns of the firms among the
wealth it wants to hold, so it does not also keep that wealth as idle cash; more of its income reaches a spender
(goods, or a producer's loan). Values are read from the economy's records, not from text.

Measured on the fixture with plant (`plant_setup`, 40 quiet years, years 5 on) by `SavingReachesASpenderTests`, which
runs the economy with and without the households' equity read: the share of the savings on offer that is lent, and
the spending over income, in each."""
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

    def test_working_capital_struck_ahead_of_the_year_leaves_no_plant_to_wait_for(self):
        economy = Economy(self.setup)
        economy.record.expansion_runs = {"producer:x": 0.0}
        economy.record.loan_requests = []
        economy._lend([], economy.view(), {}, YearLedger())
        self.assertEqual(economy.record.expansion_runs, {})


def _run_years(count_equity):
    """(spending over income, lent over offered) over the warmed-up years, with households counting what they
    own of the firms or not."""
    setup = plant_setup()
    economy = Economy(setup)
    if not count_equity:
        economy._equity_read = lambda view: {}
    economy_api.begin_spin_up(economy)
    spent = income = lent = offered = 0.0
    for year in range(YEARS):
        economy.step(fixture.quiet_year(setup))
        if year < WARM_UP_YEARS:
            continue
        record = economy.record
        spent += sum(cohort.last_year_spending for cohort in record.cohorts.values())
        income += sum(cohort.last_year_income for cohort in record.cohorts.values())
        lent += sum(record.lent_by_borrower.values())
        offered += record.funds_offered
    return spent / income, lent / offered


class SavingReachesASpenderTests(unittest.TestCase):
    """Paired runs from the same opening: the opening no longer counts the households' equity (Complaint 558), so
    an absolute bound would measure the opening's state, not the mechanism."""

    @classmethod
    def setUpClass(cls):
        cls.spending_with, cls.lent_with = _run_years(True)
        cls.spending_without, cls.lent_without = _run_years(False)

    def test_households_that_count_their_firms_spend_more_of_their_income(self):
        self.assertGreater(self.spending_with, self.spending_without)

    def test_a_share_of_the_savings_on_offer_is_lent_to_producers(self):
        self.assertGreater(self.lent_with, 0.08)
        self.assertGreater(self.lent_with, 2.0 * self.lent_without)


if __name__ == "__main__":
    unittest.main()
