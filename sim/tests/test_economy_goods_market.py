"""The economy's goods market: price where buyers' schedules meet sellers' reservations, rationing by
priority, fills that sum exactly, and a famine price that is set by budgets."""
import math
import random
import unittest

from sim.economy.goods_market import _ration_buyers, clear, quantity_at
from sim.economy.types import Bid, Offer


def bid(buyer="b1", floor=0.0, flexible=0.0, reference=1.0, elasticity=1.0, budget=1e9, priority=0):
    return Bid(buyer, "grain", "area", "tile", floor, flexible, reference, elasticity, budget, priority)


def offer(seller="s1", quantity=10.0, reservation=1.0):
    return Offer(seller, "grain", "area", "tile", quantity, reservation)


def run(bids, offers, last_price=None):
    return clear(bids, offers, "grain", "area", "coin", last_price)


def total(result, side):
    return math.fsum(fill.quantity for fill in result.fills if fill.side == side)


class QuantityAtTests(unittest.TestCase):
    def test_floor_plus_flexible_at_reference_price(self):
        self.assertAlmostEqual(quantity_at(bid(floor=3.0, flexible=5.0), 1.0), 8.0)

    def test_flexible_part_falls_with_price(self):
        self.assertAlmostEqual(quantity_at(bid(flexible=4.0, elasticity=2.0), 2.0), 1.0)

    def test_zero_elasticity_is_constant(self):
        self.assertAlmostEqual(quantity_at(bid(floor=1.0, flexible=4.0, elasticity=0.0), 50.0), 5.0)

    def test_budget_caps_quantity(self):
        self.assertAlmostEqual(quantity_at(bid(floor=10.0, budget=20.0), 4.0), 5.0)

    def test_zero_budget_buys_nothing(self):
        self.assertEqual(quantity_at(bid(floor=10.0, budget=0.0), 1.0), 0.0)


class ClearingTests(unittest.TestCase):
    def test_price_between_two_sellers_with_different_reservations(self):
        result = run([bid(flexible=12.0, elasticity=1.0)],
                     [offer("cheap", 10.0, 0.8), offer("dear", 10.0, 1.3)])
        self.assertGreater(result.price, 0.8)
        self.assertLessEqual(result.price, 1.3)
        sold = {fill.agent: fill.quantity for fill in result.fills if fill.side == "sell"}
        self.assertAlmostEqual(sold["cheap"], 10.0)
        self.assertNotIn("dear", sold)

    def test_marginal_seller_is_filled_pro_rata(self):
        result = run([bid(floor=12.0)], [offer("a", 10.0, 1.0), offer("b", 10.0, 1.0)])
        sold = {fill.agent: fill.quantity for fill in result.fills if fill.side == "sell"}
        self.assertAlmostEqual(sold["a"], 6.0)
        self.assertAlmostEqual(sold["b"], 6.0)

    def test_fills_sum_exactly(self):
        result = run([bid("x", 3.0, 4.0, budget=50.0), bid("y", 2.0, 9.0, budget=80.0)],
                     [offer("a", 5.0, 0.5), offer("b", 7.0, 1.1), offer("c", 4.0, 2.0)])
        self.assertAlmostEqual(total(result, "buy"), total(result, "sell"), places=9)
        self.assertAlmostEqual(total(result, "buy"), result.quantity, places=9)

    def test_buyers_pay_budget_at_most(self):
        result = run([bid("x", 3.0, 4.0, budget=5.0)], [offer("a", 50.0, 0.5)])
        spent = result.price * total(result, "buy")
        self.assertLessEqual(spent, 5.0 + 1e-9)

    def test_rationing_serves_the_lower_priority_number_first(self):
        # Demand is continuous, so the clearing price leaves nothing to ration; the rule applies to
        # whatever gap is left (a price held by a cap, a rounding remainder) and is tested directly.
        need, want = bid("need", floor=8.0, priority=0), bid("want", floor=8.0, priority=1)
        served = dict((item.buyer, quantity) for item, quantity in _ration_buyers([need, want], 1.0, 10.0))
        self.assertAlmostEqual(served["need"], 8.0)
        self.assertAlmostEqual(served["want"], 2.0)

    def test_rationing_is_pro_rata_within_a_tier(self):
        pair = [bid("a", floor=6.0), bid("b", floor=12.0)]
        served = dict((item.buyer, quantity) for item, quantity in _ration_buyers(pair, 1.0, 9.0))
        self.assertAlmostEqual(served["a"], 3.0)
        self.assertAlmostEqual(served["b"], 6.0)

    def test_short_supply_with_floors_only_is_shared_by_budget(self):
        result = run([bid("rich", floor=8.0, budget=800.0), bid("poor", floor=8.0, budget=200.0)],
                     [offer("a", 10.0, 1.0)])
        got = dict((fill.agent, fill.quantity) for fill in result.fills if fill.side == "buy")
        self.assertAlmostEqual(got["rich"] + got["poor"], 10.0, places=6)
        self.assertAlmostEqual(got["rich"] / got["poor"], 4.0, places=4)
        self.assertGreater(result.unmet_floor, 5.9)

    def test_unaffordable_floor_is_unmet(self):
        result = run([bid("poor", floor=10.0, budget=2.0)], [offer("s", 100.0, 1.0)])
        self.assertAlmostEqual(result.quantity, 2.0)
        self.assertAlmostEqual(result.unmet_floor, 8.0)

    def test_negative_reservation_sells_what_demand_takes_at_a_small_positive_price(self):
        result = run([bid(flexible=3.0, elasticity=1.0)], [offer("waste", 10000.0, -2.0)])
        self.assertGreater(result.price, 0.0)
        self.assertLess(result.price, 0.01)
        self.assertGreater(result.quantity, 0.0)
        self.assertLess(result.quantity, result.offered_at_price)

    def test_no_offers_leaves_price_and_all_floors_unmet(self):
        result = run([bid(floor=4.0), bid("b2", floor=1.0)], [], last_price=2.5)
        self.assertEqual(result.fills, ())
        self.assertEqual(result.price, 2.5)
        self.assertAlmostEqual(result.unmet_floor, 5.0)
        self.assertEqual(run([bid(floor=1.0)], [], None).price, 0.0)

    def test_no_bids_keeps_last_price_if_a_seller_would_sell_at_it(self):
        result = run([], [offer("a", 5.0, 1.0)], last_price=3.0)
        self.assertEqual(result.price, 3.0)
        self.assertEqual(result.quantity, 0.0)
        self.assertEqual(result.fills, ())

    def test_no_bids_and_last_price_below_every_reservation_gives_lowest_reservation(self):
        result = run([], [offer("a", 5.0, 2.0), offer("b", 5.0, 4.0)], last_price=1.0)
        self.assertEqual(result.price, 2.0)

    def test_famine_halving_supply_raises_price_more_than_proportionally(self):
        buyers = [bid("h%d" % index, floor=10.0, flexible=2.0, elasticity=0.3, budget=400.0)
                  for index in range(10)]
        normal = run(buyers, [offer("farm", 120.0, 1.0)])
        famine = run(buyers, [offer("farm", 60.0, 1.0)])
        self.assertGreater(famine.price, 2.0 * normal.price)
        self.assertLessEqual(famine.price, 4000.0 / 60.0 + 1e-6)
        self.assertGreater(famine.unmet_floor, normal.unmet_floor)

    def test_budget_limited_price_is_finite(self):
        result = run([bid(floor=1000.0, budget=100.0)], [offer("s", 5.0, 1.0)])
        self.assertAlmostEqual(result.price, 20.0, places=6)

    def test_input_order_does_not_change_the_result(self):
        rng = random.Random(7)
        bids = [bid("b%d" % index, floor=rng.uniform(0, 3), flexible=rng.uniform(0, 6),
                    reference=rng.uniform(0.5, 2), elasticity=rng.uniform(0, 2),
                    budget=rng.uniform(5, 60), priority=index % 3) for index in range(12)]
        offers = [offer("s%d" % index, rng.uniform(1, 8), rng.choice([0.5, 1.0, 1.0, 2.0])) for index in range(8)]
        first = run(bids, offers, 1.0)
        rng.shuffle(bids)
        rng.shuffle(offers)
        second = run(bids, offers, 1.0)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
