"""Household cohorts: classes from the Gini split, budgets bounded by cash, floors and crowding out,
durables as replacement, consumption and unmet floors, determinism."""
import dataclasses
import time
import unittest

from sim.economy import households
from sim.economy.types import EDGE_CONSUMPTION, GoodSpec

NEED_DATA = {
    "needs": {
        "food": {"surplus_budget_share": 0.4, "subsistence_per_capita_per_year": 200.0},
        "clothing": {"surplus_budget_share": 0.2},
        "tools": {"surplus_budget_share": 0.2},
        "spice": {"surplus_budget_share": 0.2},
    },
    "goods": {
        "grain": {"satisfies": {"food": 1.0}},
        "cloth": {"satisfies": {"clothing": 1.0}},
        "plough": {"satisfies": {"tools": 1.0}},
        "pepper": {"satisfies": {"spice": 1.0}},
    },
}
SPECS = {
    "grain": GoodSpec("grain", 1.0, 0.1, 0.0, "food"),
    "cloth": GoodSpec("cloth", 1.0, 0.0, 0.0, "cloth"),
    "plough": GoodSpec("plough", 10.0, 0.0, 5.0, "tool"),
    "pepper": GoodSpec("pepper", 1.0, 0.0, 0.0, "spice"),
}
BASKET = households.make_basket(NEED_DATA, {})


class View:
    year = 1

    def __init__(self, prices=None, stocks=None):
        self.prices = {"grain": 1.0, "cloth": 2.0, "plough": 5.0, "pepper": 4.0}
        self.prices.update(prices or {})
        self.stocks = stocks or {}

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return 1.0

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area:" + good

    def currency_of(self, area):
        return "coin"

    def price_level(self, currency):
        return 1.0

    def expected_inflation(self, currency):
        return 0.0

    def cash(self, agent, currency):
        return 0.0

    def stock(self, agent, good, tile):
        return self.stocks.get((agent, good, tile), 0.0)


def cohort(people=100.0, **changes):
    base = households.Cohort("household:t:0", "t", 0, people, people / 2, 0.3)
    return dataclasses.replace(base, **changes)


def budget_total(orders):
    return sum(bid.budget for bid in orders.bids)


def bid_for(orders, good):
    return next((bid for bid in orders.bids if bid.good == good), None)


class CohortSplitTests(unittest.TestCase):
    def test_classes_partition_people_and_income_by_the_gini_split(self):
        cohorts = households.cohorts_for_tile("t", 900.0, 0.5, 0.4, 3)
        self.assertEqual(len(cohorts), 3)
        self.assertAlmostEqual(sum(c.people for c in cohorts), 900.0)
        self.assertAlmostEqual(sum(c.working_people for c in cohorts), 450.0)
        self.assertAlmostEqual(sum(c.ownership_share for c in cohorts), 1.0)
        shares = [c.ownership_share for c in cohorts]
        self.assertEqual(shares, sorted(shares))                 # poorest first

    def test_higher_gini_gives_the_poorest_class_less(self):
        low = households.cohorts_for_tile("t", 900.0, 0.5, 0.3, 3)
        high = households.cohorts_for_tile("t", 900.0, 0.5, 0.6, 3)
        self.assertGreater(low[0].ownership_share, high[0].ownership_share)

    def test_property_income_follows_ownership(self):
        cohorts = households.cohorts_for_tile("t", 900.0, 0.5, 0.4, 3)
        paid = households.distribute_property_income(cohorts, 100.0)
        self.assertAlmostEqual(sum(paid.values()), 100.0)
        self.assertGreater(paid[cohorts[2].agent_id], paid[cohorts[0].agent_id])

    def test_ids_are_deterministic(self):
        first = households.cohorts_for_tile("t", 900.0, 0.5, 0.4, 3)
        second = households.cohorts_for_tile("t", 900.0, 0.5, 0.4, 3)
        self.assertEqual(first, second)
        self.assertEqual(len({c.agent_id for c in first}), 3)


class LabourTests(unittest.TestCase):
    def test_one_offer_per_trade_with_danger_raising_the_reservation(self):
        offers = households.labour_offers(cohort(), {"smith": 10.0, "miner": 5.0, "idle": 0.0}, View(),
                                          200.0, 2000.0, {"miner": 0.01})
        self.assertEqual([offer.trade for offer in offers], ["miner", "smith"])
        miner, smith = offers
        self.assertGreater(miner.reservation_wage, smith.reservation_wage)
        self.assertAlmostEqual(smith.reservation_wage, 0.1)
        self.assertAlmostEqual(smith.hours, 20000.0)


class GoodsOrderTests(unittest.TestCase):
    def orders(self, cash=1000.0, income=1000.0, view=None, **changes):
        return households.goods_orders(cohort(**changes), view or View(), cash, income, BASKET, SPECS)

    def test_budgets_never_exceed_cash(self):
        for cash in (0.0, 10.0, 150.0, 20000.0, 1e6):
            for income in (0.0, 50.0, 20000.0):
                orders = self.orders(cash=cash, income=income)
                self.assertLessEqual(budget_total(orders), cash + 1e-9, (cash, income))

    def test_floor_is_subsistence_times_people_and_met_when_affordable(self):
        orders = self.orders(cash=30000.0, income=30000.0)
        grain = bid_for(orders, "grain")
        self.assertAlmostEqual(grain.floor_quantity, 200.0 * 100.0)
        self.assertGreaterEqual(grain.budget, grain.floor_quantity * grain.reference_price)

    def test_poor_cohort_bids_only_for_the_floor_and_goes_short(self):
        orders = self.orders(cash=5000.0, income=5000.0)         # floor costs 20000
        self.assertEqual([bid.good for bid in orders.bids], ["grain"])
        self.assertLessEqual(orders.bids[0].budget, 5000.0)

    def test_price_rise_in_a_necessity_crowds_out_luxuries(self):
        base = self.orders(cash=40000.0, income=40000.0)
        dear = self.orders(cash=40000.0, income=40000.0, view=View({"grain": 1.4}))
        for good in ("cloth", "pepper"):
            self.assertLess(bid_for(dear, good).flexible_quantity, bid_for(base, good).flexible_quantity)

    def test_poor_buys_fewer_luxuries_than_rich(self):
        poor = households.goods_orders(cohort(), View(), 21000.0, 21000.0, BASKET, SPECS)
        rich = households.goods_orders(cohort(), View(), 60000.0, 60000.0, BASKET, SPECS)
        poor_luxury = bid_for(poor, "pepper").flexible_quantity if bid_for(poor, "pepper") else 0.0
        self.assertGreater(bid_for(rich, "pepper").flexible_quantity, poor_luxury)

    def test_cash_above_target_raises_spending(self):
        base = self.orders(cash=30000.0, income=30000.0, cash_target=30000.0)
        rich_in_cash = self.orders(cash=90000.0, income=30000.0, cash_target=30000.0)
        self.assertGreater(sum(b.flexible_quantity * b.reference_price for b in rich_in_cash.bids),
                           sum(b.flexible_quantity * b.reference_price for b in base.bids))

    def test_savings_above_target_are_offered_at_expected_inflation(self):
        orders = self.orders(cash=1e6, income=1000.0, cash_target=1000.0, expected_inflation=0.02)
        self.assertEqual(len(orders.funds_offers), 1)
        self.assertAlmostEqual(orders.funds_offers[0].minimum_rate, 0.02)
        self.assertLessEqual(budget_total(orders) + orders.funds_offers[0].amount, 1e6 + 1e-6)

    def test_durable_demand_is_replacement(self):
        none_held = bid_for(self.orders(cash=60000.0, income=60000.0), "plough")
        view = View(stocks={("household:t:0", "plough", "t"): 1e9})
        full = bid_for(self.orders(cash=60000.0, income=60000.0, view=view), "plough")
        self.assertGreater(none_held.flexible_quantity, 0.0)
        self.assertIsNone(full)                                   # a stock beyond target needs no more

    def test_durable_at_target_is_replaced_at_its_wear_rate(self):
        orders = self.orders(cash=60000.0, income=60000.0)
        flow = bid_for(orders, "plough").flexible_quantity / 5.0   # target stock is five years of flow
        view = View(stocks={("household:t:0", "plough", "t"): 5.0 * flow})
        steady = bid_for(self.orders(cash=60000.0, income=60000.0, view=view), "plough")
        self.assertAlmostEqual(steady.flexible_quantity, flow, places=6)

    def test_determinism(self):
        self.assertEqual(self.orders(), self.orders())

    def test_unpriced_goods_are_not_bid_for(self):
        view = View()
        view.prices.pop("pepper")
        self.assertIsNone(bid_for(self.orders(view=view), "pepper"))

    def test_time_of_one_cohort(self):
        start = time.perf_counter()
        for _ in range(200):
            self.orders()
        self.assertLess((time.perf_counter() - start) / 200, 0.01)


class CloseTests(unittest.TestCase):
    def test_non_durables_are_consumed_and_durables_kept(self):
        view = View(stocks={("household:t:0", "plough", "t"): 3.0})
        new, moves = households.close_year(cohort(), {"grain": 20000.0, "plough": 3.0}, view, SPECS, BASKET)
        self.assertEqual([move.good for move in moves], ["grain"])
        self.assertEqual(moves[0].receiver, EDGE_CONSUMPTION)
        self.assertEqual(moves[0].tile, "t")
        self.assertEqual(new.unmet_floor_by_need, {})

    def test_unmet_floor_is_recorded_when_short(self):
        new, _ = households.close_year(cohort(), {"grain": 15000.0}, View(), SPECS, BASKET)
        self.assertAlmostEqual(new.unmet_floor_by_need["food"], 5000.0)

    def test_expected_inflation_follows_the_price_level(self):
        view = View()
        view.price_level = lambda currency: 1.1
        new, _ = households.close_year(cohort(), {"grain": 20000.0}, view, SPECS, BASKET,
                                       income_received=100.0, spent=90.0)
        self.assertGreater(new.expected_inflation, 0.0)
        self.assertEqual((new.last_year_income, new.last_year_spending), (100.0, 90.0))
        self.assertGreater(new.cash_target, 0.0)


if __name__ == "__main__":
    unittest.main()
