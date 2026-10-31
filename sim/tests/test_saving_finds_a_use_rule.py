"""Complaints 605 and 607 (Complaint 640 rules): `equity.holdings` shares a firm's net worth among its owners by ownership
share, and `goods_orders` counts what a cohort owns of firms as wealth it already holds: it spends more and offers less idle
cash for loan. Each is called on inputs built here."""
import dataclasses
import unittest
from types import SimpleNamespace

from sim.book import Book, Transfer
from sim.economy import equity, households
from sim.economy.types import GoodSpec

QUICK_TOPIC = True
SURPLUS_FACTOR = 20.0
MONEY = "coin"
TILE = "t"
LAST_YEAR_INCOME = 100000.0

NEED_DATA = {
    "needs": {"food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 200.0},
              "adornment": {"surplus_budget_share": 0.5}},
    "goods": {"grain": {"satisfies": {"food": 1.0}}, "beads": {"satisfies": {"adornment": 1.0}}},
}
SPECS = {name: GoodSpec(name, 1.0, 0.0, 0.0, name) for name in ("grain", "beads")}
BASKET = households.make_basket(NEED_DATA, {})


class OwningView:
    """What `goods_orders` reads of the market, with every agent owning `worth` of the firms."""
    year = 1

    def __init__(self, worth):
        self.worth = worth

    def price(self, good, area):
        return {"grain": 1.0, "beads": 2.0}.get(good)

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area:" + good

    def currency_of(self, area):
        return MONEY

    def stock(self, agent, good, tile):
        return 0.0

    def equity(self, agent):
        return self.worth


def cohort_of(income_class, ownership_share):
    return households.Cohort("household:t:%d" % income_class, TILE, income_class, 1000.0, 500.0, ownership_share,
                             last_year_income=LAST_YEAR_INCOME)


def orders_with_worth(worth):
    """The orders of one cohort with an income well above its floors, owning `worth` of the firms."""
    cohort = dataclasses.replace(cohort_of(0, 0.3), expected_spending=0.0)    # no habit of spending to hold it up
    income = SURPLUS_FACTOR * cohort.last_year_income
    view = OwningView(worth)
    return households.goods_orders(cohort, view, income, income, BASKET, SPECS, smooth_rise=False)


class EquityTests(unittest.TestCase):
    def test_the_owners_share_the_net_worth_of_their_firms_by_ownership_share(self):
        book = Book()
        book.transfer(Transfer("edge:mint", "producer:one", MONEY, 900.0, "opening"))
        book.transfer(Transfer("edge:mint", "producer:two", MONEY, 300.0, "opening"))
        cohorts = {each.agent_id: each for each in (cohort_of(0, 0.1), cohort_of(1, 0.2), cohort_of(2, 0.7))}
        no_plant = SimpleNamespace(plant_life_years=0.0)
        record = SimpleNamespace(
            cohorts=cohorts, loans=[], shares={}, book=book, capital=SimpleNamespace(share_price_factor=1.0),
            producers={"producer:one": SimpleNamespace(owner="household:t:2", capacity_runs=1.0, recipe_id="farm"),
                       "producer:two": SimpleNamespace(owner="household:t:0", capacity_runs=1.0, recipe_id="farm")})
        setup = SimpleNamespace(currency_id=MONEY, recipes={"farm": no_plant})
        held = equity.holdings(setup, record, None)
        total = 900.0 + 300.0
        self.assertAlmostEqual(sum(held.values()), total, delta=1e-6 * total)
        ratios = [held[agent] / cohorts[agent].ownership_share for agent in cohorts]
        for ratio in ratios:
            self.assertAlmostEqual(ratio, ratios[0], delta=1e-6 * ratios[0])

    def test_a_cohort_that_owns_firms_spends_more_than_one_that_owns_none(self):
        owns = sum(bid.budget for bid in orders_with_worth(10.0 * SURPLUS_FACTOR * 100.0 * LAST_YEAR_INCOME).bids)
        none = sum(bid.budget for bid in orders_with_worth(0.0).bids)
        self.assertGreater(owns, none)

    def test_a_cohort_that_owns_firms_keeps_less_idle_cash_to_offer_for_loan(self):
        owns = sum(offer.amount for offer in orders_with_worth(10.0 * SURPLUS_FACTOR * 100.0 * LAST_YEAR_INCOME).funds_offers)
        none = sum(offer.amount for offer in orders_with_worth(0.0).funds_offers)
        self.assertGreater(none, 0.0)
        self.assertLess(owns, none)


if __name__ == "__main__":
    unittest.main()
