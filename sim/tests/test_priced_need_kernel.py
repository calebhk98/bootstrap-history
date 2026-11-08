"""Numba port, the household basket's needs priced on a tile: `priced_needs.priced_needs` (the kernel over the need and good tables)
equals `need_basket.need_prices` / `priced_need` (the Python) bit for bit, on written-out needs and on random ones with qualities, share
limits, missing and zero prices. No game."""

QUICK_TOPIC = True

import dataclasses
import math
import random
import unittest

import numpy as np

from sim.economy import priced_need_tables, priced_needs
from sim.world import need_basket
from sim.world.need_basket import Basket, NeedSpec


def basket_of(specs, substitution=2.0):
    return Basket(tuple(specs), substitution, {})


def compare(test, specs, prices, substitution=2.0, reach=0.0):
    """The kernel's priced needs and the Python's, for the same needs, prices and reach: equal field by field, exactly."""
    basket = basket_of(specs, substitution)
    exponent = 1.0 - substitution
    expected = [priced for priced in (need_basket.priced_need(spec, exponent, prices.get, quality_reach=reach) for spec in specs)
                if priced is not None]
    pack = priced_need_tables.pack_needs(specs)
    vector = priced_need_tables.price_vector(pack, prices.get)
    got = priced_needs.priced_needs(pack, vector, basket, reach)
    test.assertEqual(len(got), len(expected))
    for left, right in zip(got, expected):
        test.assertEqual(left.spec, right.spec)
        test.assertEqual(left.price_index, right.price_index)
        test.assertEqual(left.goods, right.goods)
        test.assertEqual(left.ceilings, right.ceilings)
    return expected


class WrittenOutTests(unittest.TestCase):
    FOOD = NeedSpec("food", 200.0, 0.5, (("grain", 1.0), ("tallow", 2.0)))

    def test_two_goods_one_unlimited_need(self):
        (need,) = compare(self, [self.FOOD], {"grain": 1.0, "tallow": 0.2})
        self.assertAlmostEqual(sum(row[3] for row in need.goods), 1.0)

    def test_a_good_without_a_price_or_with_a_zero_price_is_left_out(self):
        (need,) = compare(self, [self.FOOD], {"grain": 1.0, "tallow": 0.0})
        self.assertEqual([row[0] for row in need.goods], ["grain"])
        self.assertEqual(need.ceilings, (math.inf,))

    def test_a_need_with_no_priced_good_is_not_in_the_answer(self):
        self.assertEqual(compare(self, [self.FOOD], {}), [])

    def test_a_binding_limit_moves_spending_to_the_other_good(self):
        limited = NeedSpec("food", 200.0, 0.5, (("grain", 1.0), ("tallow", 2.0)), (("tallow", 0.35),))
        free, capped = compare(self, [self.FOOD], {"grain": 1.0, "tallow": 0.2}), compare(self, [limited], {"grain": 1.0, "tallow": 0.2})
        self.assertGreater(capped[0].price_index, free[0].price_index)

    def test_a_limit_that_does_not_bind_changes_nothing(self):
        limited = NeedSpec("food", 200.0, 0.5, (("grain", 1.0), ("tallow", 2.0)), (("tallow", 0.999),))
        self.assertEqual(compare(self, [limited], {"grain": 1.0, "tallow": 0.2})[0].goods,
                         compare(self, [self.FOOD], {"grain": 1.0, "tallow": 0.2})[0].goods)

    def test_quality_re_mix(self):
        light = NeedSpec("light", 0.0, 0.1, (("tallow", 1.0), ("oil", 1.3), ("wax", 0.9)), (), (("tallow", 0.7), ("oil", 0.85)))
        for reach in (0.0, 0.3, 1.0):
            compare(self, [light], {"tallow": 0.9, "oil": 1.7, "wax": 2.2}, reach=reach)

    def test_quality_and_limits_together(self):
        light = NeedSpec("light", 0.0, 0.1, (("tallow", 1.0), ("oil", 1.3), ("wax", 0.9)), (("tallow", 0.2), ("wax", 0.3)),
                         (("tallow", 0.7), ("oil", 0.85)))
        compare(self, [light], {"tallow": 0.1, "oil": 1.7, "wax": 0.5}, reach=0.6)

    def test_limits_that_cannot_all_be_met_still_agree(self):
        every = NeedSpec("food", 200.0, 0.5, (("a", 1.0), ("b", 1.0)), (("a", 0.2), ("b", 0.2)))
        compare(self, [every], {"a": 1.0, "b": 2.0})


def random_needs(rng):
    goods = ["g%d" % number for number in range(rng.randint(2, 9))]
    specs = []
    for number in range(rng.randint(1, 4)):
        chosen = rng.sample(goods, rng.randint(1, min(5, len(goods))))
        limits = tuple((good, rng.uniform(0.05, 0.9)) for good in chosen if rng.random() < 0.35)
        qualities = tuple((good, rng.uniform(0.3, 1.2)) for good in chosen if rng.random() < 0.4)
        specs.append(NeedSpec("need%d" % number, rng.choice([0.0, 200.0]), rng.uniform(0.0, 1.0),
                              tuple((good, rng.choice([0.0, rng.uniform(0.1, 3.0), rng.uniform(0.1, 3.0)])) for good in chosen), limits, qualities))
    prices = {good: rng.choice([None, 0.0, rng.uniform(0.05, 20.0), rng.uniform(0.05, 20.0), rng.uniform(0.05, 20.0)]) for good in goods}
    return specs, {good: price for good, price in prices.items() if price is not None}


class RandomTests(unittest.TestCase):
    def test_kernel_equals_the_python_bit_for_bit(self):
        rng = random.Random(11)
        limited = qualified = priced_count = binding = 0
        for _case in range(600):
            specs, prices = random_needs(rng)
            reach = rng.choice([0.0, rng.random(), 1.0])
            substitution = rng.choice([2.0, 3.5, 0.5, 5.0])
            expected = compare(self, specs, prices, substitution, reach)
            priced_count += len(expected)
            limited += any(spec.share_limits for spec in specs)
            stripped = [need_basket.priced_need(dataclasses.replace(spec, share_limits=()), 1.0 - substitution, prices.get, quality_reach=reach)
                        for spec in specs if spec.share_limits]
            binding += sum(1 for one, other in zip(stripped, [need for need in expected if need.spec.share_limits])
                           if one is not None and other.goods != one.goods)
            qualified += any(spec.qualities for spec in specs) and reach > 0.0
        self.assertGreater(priced_count, 500)
        self.assertGreater(limited, 100)
        self.assertGreater(qualified, 50)
        self.assertGreater(binding, 50, "limits that bind are exercised")

    def test_the_price_vector_has_nan_for_a_good_without_a_price(self):
        pack = priced_need_tables.pack_needs([NeedSpec("food", 1.0, 1.0, (("a", 1.0), ("b", 1.0)))])
        vector = priced_need_tables.price_vector(pack, {"a": 2.0}.get)
        self.assertEqual(vector[0], 2.0)
        self.assertTrue(np.isnan(vector[1]))


if __name__ == "__main__":
    unittest.main()
