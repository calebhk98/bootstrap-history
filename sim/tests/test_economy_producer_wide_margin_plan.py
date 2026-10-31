"""A maker whose output pays far above its cost, with inputs on sale and cash in hand, plans every run its
year's change allows and bids for its inputs above their price. So when such a maker (carts, bar iron) shows no
runs while its price climbs, the limit is outside `producers.plan`: its inputs were not delivered (Complaints/473)."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers
from sim.economy.types import Recipe

CART = Recipe("cart", {"cart": 1.0}, {"bar": 15.0, "timber": 0.4}, {"carpenter": 150.0, "smith": 15.0})


class View:
    year = 3

    def __init__(self, prices, wages):
        self.prices, self.wages = prices, wages

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def basket_price_level(self, currency):
        return 1.0

    def expected_inflation(self, currency):
        return 0.0

    def cash(self, agent, currency):
        return 0.0

    def stock(self, agent, good, tile):
        return 0.0


def cart_maker(**changes):
    base = dict(agent_id="c1", owner="lord", recipe_id="cart", tile="t", capacity_runs=100.0, last_runs=0.0,
                expected_sales=1.0, expected_prices={"cart": 1000.0, "bar": 4.0, "timber": 70.0})
    base.update(changes)
    return producers.Producer(**base)


def wide_margin_view():
    # a run costs about 60 + 28 + 170 and sells for 1000
    return View({"cart": 1000.0, "bar": 4.0, "timber": 70.0}, {"carpenter": 1.0, "smith": 1.0})


class WideMarginPlanTests(unittest.TestCase):
    def test_a_maker_idle_last_year_plans_its_expected_sales_and_refill_and_the_price_is_no_limit(self):
        who = cart_maker()
        plan = producers.plan(who, CART, wide_margin_view(), 1e6)
        self.assertAlmostEqual(plan.runs, producers.runs_for_stock(who, CART, wide_margin_view()))
        self.assertLess(plan.runs, producers.OUTPUT_CHANGE_SHARE_PER_YEAR * who.capacity_runs)       # expected sales bind, not the margin
        wanted_at_price = who.capacity_runs * producers.share_working(1000.0, 4.0 * 15.0 + 70.0 * 0.4 + 165.0)
        self.assertGreater(wanted_at_price, 0.99 * who.capacity_runs)         # the price is no limit
        self.assertGreater(producers.runs_for_stock(who, CART, wide_margin_view()), who.expected_sales)

    def test_the_input_bids_of_such_a_maker_are_ceilinged_above_the_input_prices_by_the_margin_share_each_input_accounts_for(self):
        plan = producers.plan(cart_maker(), CART, wide_margin_view(), 1e6)
        ceilings = {bid.good: bid.maximum_price for bid in plan.bids}
        self.assertGreater(ceilings["bar"], 2.0 * 4.0)
        self.assertGreater(ceilings["timber"], 2.0 * 70.0)
        self.assertLess(ceilings["bar"], 10.0 * 4.0)      # not the whole run margin over the input's share of the run (test_economy_input_ceiling_share)

    def test_the_labour_bids_are_for_every_planned_run(self):
        plan = producers.plan(cart_maker(), CART, wide_margin_view(), 1e6)
        hours = {bid.trade: bid.hours for bid in plan.labour_bids}
        self.assertAlmostEqual(hours["carpenter"], 150.0 * plan.runs)
        self.assertAlmostEqual(hours["smith"], 15.0 * plan.runs)


if __name__ == "__main__":
    unittest.main()
