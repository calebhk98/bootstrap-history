"""Numba port, households' respend: the bids one rationed buyer places (`goods_respend_basket_kernel.price_basket` and `place_priced_bids`) are the bids
`goods_respend.respend_bids` makes (the money of a need split over its goods still offered by the basket's choice rule and
share limits, the money of a need with none offered passed to the others, a ceiling at the next cheapest good's parity), on
random baskets, asks and rationed money. No game.

A relative tolerance is needed because the kernel sums left to right where the old path used `math.fsum`."""

QUICK_TOPIC = True

import math
import random
import unittest

import numpy

from sim.economy import goods_respend, goods_respend_basket_kernel, goods_respend_pack
from sim.tests.respend_plain import plain_flatten_baskets
from sim.world.need_basket import Basket, NeedSpec

GOODS = ["bread", "cloth", "fish", "oil", "salt", "wine"]     # sorted, as the pack numbers them
TOLERANCE = 1e-9


def random_basket(rng):
    needs = []
    for index in range(rng.randint(1, 4)):
        served = rng.sample(GOODS, rng.randint(1, 4))
        goods = tuple((good, rng.choice([0.5, 1.0, 2.0, rng.uniform(0.2, 3.0)])) for good in served)
        limits = tuple((good, rng.uniform(0.2, 0.7)) for good, _effect in goods if rng.random() < 0.3)
        needs.append(NeedSpec("need%d" % index, rng.choice([0.0, 1.0]), rng.uniform(0.5, 3.0), goods, share_limits=limits))
    return Basket(needs=tuple(needs), substitution=rng.choice([0.4, 1.0, 1.3, 2.0, 3.5]), need_data={})


class FlattenedBasketsAreTheTripleLoops(unittest.TestCase):

    def test_random_baskets(self):
        rng = random.Random(9)
        good_index = {good: index for index, good in enumerate(GOODS)}
        for _case in range(200):
            baskets = [random_basket(rng) for _each in range(rng.randint(1, 5))]
            got, expected = goods_respend_pack.flatten_baskets(baskets, good_index), plain_flatten_baskets(baskets, good_index)
            self.assertEqual([each.tolist() if hasattr(each, "tolist") else each for each in got],
                             [each.tolist() if hasattr(each, "tolist") else each for each in expected])
            self.assertEqual([each.dtype for each in got[:-1]], [each.dtype for each in expected[:-1]])


class BuyerBidsAreTheRespendBids(unittest.TestCase):

    def test_random_baskets(self):
        rng = random.Random(5)
        compared = 0
        for _case in range(400):
            basket = random_basket(rng)
            good_index = {good: index for index, good in enumerate(GOODS)}
            flat = goods_respend_pack.flatten_baskets([basket], good_index)
            asks = {good: rng.uniform(0.3, 9.0) for good in GOODS if rng.random() < 0.7}
            rationed = {spec.need_id: rng.choice([0.0, rng.uniform(1.0, 200.0)]) for spec in basket.needs}
            old = goods_respend.respend_bids("h", "t", basket, rationed, asks, lambda good: "area")
            ask_of_good = numpy.array([asks.get(good, numpy.nan) for good in GOODS])
            rows = len(flat[5])
            scratch = [numpy.zeros(rows), numpy.zeros(rows), numpy.zeros(rows, dtype=numpy.bool_), numpy.zeros(rows),
                       numpy.zeros(rows), numpy.zeros(rows, dtype=numpy.bool_)]
            spend, ceiling = numpy.zeros(len(GOODS)), numpy.zeros(len(GOODS))
            out_good, out_spend, out_ceiling = numpy.zeros(len(GOODS), dtype=numpy.int64), numpy.zeros(len(GOODS)), numpy.zeros(len(GOODS))
            money = numpy.array([rationed[spec.need_id] for spec in basket.needs])
            need_priced = numpy.zeros(len(flat[1]), dtype=numpy.int64)
            goods_respend_basket_kernel.price_basket(
                0, flat[0], flat[4], flat[3], flat[5], flat[6], flat[7], flat[8], flat[9][0], ask_of_good, *scratch,
                need_priced)
            count = goods_respend_basket_kernel.place_priced_bids(
                0, money, flat[0], flat[1], flat[4], need_priced, flat[5], scratch[2], scratch[0], scratch[1], spend,
                ceiling, numpy.zeros(len(GOODS), dtype=numpy.bool_), out_good, out_spend, out_ceiling)
            self.assertEqual([GOODS[good] for good in out_good[:count]], [bid.good for bid in old])
            for index, bid in enumerate(old):
                self.assertAlmostEqual(out_spend[index], bid.budget, delta=TOLERANCE * max(1.0, bid.budget))
                if math.isinf(bid.maximum_price):
                    self.assertTrue(math.isinf(out_ceiling[index]))
                else:
                    self.assertAlmostEqual(out_ceiling[index], bid.maximum_price, delta=TOLERANCE * bid.maximum_price)
            compared += bool(old)
        self.assertGreater(compared, 150)


if __name__ == "__main__":
    unittest.main()
