"""A household's demand for a good, and for a durable, moves continuously with price and holding
(sim/economy/households_ability.py `affordability`, `affordable_goods`; sim/economy/durable_stock.py
`purchase_toward_stock`)."""

QUICK_TOPIC = True

import unittest

import math

from sim.economy import opening_demand_kernel
from sim.economy.durable_stock import (DURABLE_GAP_CLOSED_SHARE, after_year_end_losses, gap_share, one_wear_pace, purchase_toward_stock,
                                       unpaced,
                                       replacement_for_flow)
from sim.economy.households_ability import affordability, affordable_goods, bid_cap
from sim.economy.types import GoodSpec

BUDGET = 100.0
LIFE = 10.0


class AffordabilityTest(unittest.TestCase):

    def test_share_is_continuous_and_never_rises_with_price_through_the_old_threshold(self):
        prices = [BUDGET * (0.5 + 0.001 * step) for step in range(1001)]
        shares = [affordability(price, BUDGET) for price in prices]
        for lower, higher in zip(shares, shares[1:]):
            self.assertLessEqual(higher, lower)
            self.assertLess(lower - higher, 0.01)
        self.assertGreater(shares[0], 0.9)
        self.assertLess(shares[-1], 0.1)

    def test_a_durable_within_its_service_life_budget_is_affordable(self):
        self.assertGreater(affordability(5.0 * BUDGET, BUDGET, LIFE), 0.99)
        self.assertLess(affordability(5.0 * BUDGET, BUDGET), 0.01)

    def test_a_durable_far_above_its_life_budget_is_not_affordable(self):
        self.assertEqual(affordability(1e60 * BUDGET, BUDGET, LIFE), 0.0)

    def test_no_budget_affords_nothing(self):
        self.assertEqual(affordability(1.0, 0.0), 0.0)

    def test_a_need_with_a_floor_is_never_dropped_entirely(self):
        goods = (("ox", 1e60, 1.0, 1.0),)
        affordable, _share, cap = affordable_goods(goods, BUDGET, True)
        self.assertEqual(affordable, {"ox": 1.0})
        self.assertEqual(cap, float("inf"))

    def test_a_durable_price_spread_over_its_life_is_compared_with_the_yearly_budget(self):
        goods = (("ox", 5.0 * BUDGET, 1.0, 1.0),)
        affordable, _share, _cap = affordable_goods(goods, BUDGET, False, {"ox": LIFE})
        self.assertGreater(affordable["ox"], 0.99)

    def test_a_durable_may_be_bid_up_to_its_budget_over_its_life(self):
        self.assertEqual(bid_cap(BUDGET, LIFE), BUDGET * LIFE)
        self.assertEqual(bid_cap(BUDGET, 0.0), BUDGET)


class PurchaseTowardStockTest(unittest.TestCase):
    SPEC = GoodSpec("ox", 1.0, 0.0, LIFE, "tool")
    FLOW = 5.0

    def after_losses(self, holding):
        return after_year_end_losses(holding, self.SPEC)

    def test_bid_is_continuous_in_the_held_stock(self):
        bids = [purchase_toward_stock(self.FLOW, 0.1 * step, self.SPEC) for step in range(0, 1001)]
        for before, after in zip(bids, bids[1:]):
            self.assertLess(abs(after - before), 0.05)
            self.assertLessEqual(after, before)

    def test_bid_at_the_stock_the_flow_leaves_after_wear_is_the_replacement(self):
        held = self.after_losses(self.FLOW * LIFE)
        self.assertGreater(purchase_toward_stock(self.FLOW, held, self.SPEC), 0.0)
        self.assertAlmostEqual(purchase_toward_stock(self.FLOW, held, self.SPEC), replacement_for_flow(self.FLOW, self.SPEC))

    def test_a_holding_above_the_wanted_stock_still_buys_the_replacement_and_never_sells(self):
        self.assertAlmostEqual(purchase_toward_stock(self.FLOW, 1e6, self.SPEC), replacement_for_flow(self.FLOW, self.SPEC))

    def test_an_empty_household_buys_the_replacement_and_a_share_of_the_gap(self):
        gap = self.after_losses(self.FLOW * LIFE)
        self.assertAlmostEqual(purchase_toward_stock(self.FLOW, 0.0, self.SPEC),
                               replacement_for_flow(self.FLOW, self.SPEC) + DURABLE_GAP_CLOSED_SHARE * gap)

    def test_gap_is_closed_over_several_years_without_overshooting(self):
        wanted = self.after_losses(self.FLOW * LIFE)
        held = 0.0
        years_below_nine_tenths = 0
        for _year in range(300):
            held = self.after_losses(held + purchase_toward_stock(self.FLOW, held, self.SPEC))
            self.assertLessEqual(held, wanted + 1e-9)
            if held < 0.9 * wanted:
                years_below_nine_tenths += 1
        self.assertGreater(years_below_nine_tenths, 1)
        self.assertAlmostEqual(held, wanted, places=6)

    def test_paced_by_wear_the_gap_term_moves_the_purchase_by_less_than_the_wanted_stock_moved(self):
        # a holding short of the wanted stock by a hundredth of it: unpaced, the purchase rises by many times a
        # hundredth of the flow; paced by wear, by under a hundredth of it
        spec = GoodSpec("steel", 1.0, 0.0, 30.0, "tool")
        wanted = after_year_end_losses(self.FLOW * 30.0, spec)
        base = replacement_for_flow(self.FLOW, spec)
        unpaced_rise = purchase_toward_stock(self.FLOW, 0.99 * wanted, spec) - base
        paced_rise = purchase_toward_stock(self.FLOW, 0.99 * wanted, spec, wear_paces=1.0) - base
        self.assertAlmostEqual(unpaced_rise, DURABLE_GAP_CLOSED_SHARE * 0.01 * wanted)
        self.assertGreater(unpaced_rise, 0.1 * self.FLOW)
        self.assertAlmostEqual(paced_rise, 0.01 * wanted / 30.0)
        self.assertLess(paced_rise, 0.01 * self.FLOW)

    def test_paced_by_wear_a_holding_at_the_wanted_stock_still_buys_the_replacement(self):
        spec = GoodSpec("steel", 1.0, 0.0, 30.0, "tool")
        held = after_year_end_losses(self.FLOW * 30.0, spec)
        self.assertAlmostEqual(purchase_toward_stock(self.FLOW, held, spec, wear_paces=1.0), replacement_for_flow(self.FLOW, spec))

    def test_a_good_with_no_service_life_buys_the_flow(self):
        self.assertEqual(purchase_toward_stock(self.FLOW, 3.0, GoodSpec("bread", 1.0, 0.0, 0.0, "food")), self.FLOW)




class GapShareTest(unittest.TestCase):
    def test_unpaced_it_is_the_declared_share_whatever_the_life(self):
        self.assertEqual(unpaced(), math.inf)
        self.assertEqual(gap_share(30.0, unpaced()), DURABLE_GAP_CLOSED_SHARE)
        self.assertEqual(gap_share(2.0, unpaced()), DURABLE_GAP_CLOSED_SHARE)

    def test_paced_by_wear_a_long_lived_good_closes_one_over_its_life_a_year(self):
        self.assertEqual(one_wear_pace(), 1.0)
        self.assertAlmostEqual(gap_share(30.0, one_wear_pace()), 1.0 / 30.0)

    def test_paced_by_wear_a_short_lived_good_keeps_the_declared_share(self):
        self.assertEqual(gap_share(2.0, one_wear_pace()), DURABLE_GAP_CLOSED_SHARE)

    def test_a_good_with_no_life_has_the_declared_share(self):
        self.assertEqual(gap_share(0.0, one_wear_pace()), DURABLE_GAP_CLOSED_SHARE)


class KernelTwinTest(unittest.TestCase):
    def test_the_kernels_purchase_is_the_plain_one_at_the_same_share(self):
        spec = GoodSpec("steel", 1.0, 0.0, 30.0, "tool")
        for held in (0.0, 40.0, 140.0, 400.0):
            for paces in (unpaced(), one_wear_pace()):
                self.assertAlmostEqual(
                    opening_demand_kernel._purchase_toward_stock(5.0, held, 30.0, 0.0, gap_share(30.0, paces)),
                    purchase_toward_stock(5.0, held, spec, wear_paces=paces))

    def test_the_kernels_share_is_the_plain_one(self):
        for life in (2.0, 15.0, 30.0, 100.0):
            for paces in (unpaced(), one_wear_pace()):
                self.assertAlmostEqual(opening_demand_kernel._gap_share(life, DURABLE_GAP_CLOSED_SHARE, paces), gap_share(life, paces))


if __name__ == "__main__":
    unittest.main()
