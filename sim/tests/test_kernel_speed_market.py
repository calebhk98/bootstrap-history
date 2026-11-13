"""The goods market kernels that skip repeated work (`choice_weights`, `requested_round_one`, `allocate_arrays` price a run of equal asks
once) against the plain versions they replaced, on seeded random books with many equal asks: the same bits."""
QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy import goods_market_kernels as kernels
from sim.tests import kernel_speed_plain as plain


def random_market(rng):
    """(asks ascending with runs of equal values, quantities, buyer columns, tier bounds, capped)."""
    offers, bids = rng.randint(1, 14), rng.randint(1, 9)
    levels = sorted(rng.uniform(0.5, 8.0) for _ in range(rng.randint(1, 4)))
    asks = numpy.array(sorted(rng.choice(levels) for _ in range(offers)))
    quantities = numpy.array([rng.choice([0.0, rng.uniform(0.5, 30.0)]) for _ in range(offers)])
    floors = numpy.array([rng.uniform(0.0, 4.0) for _ in range(bids)])
    flexibles = numpy.array([rng.choice([0.0, rng.uniform(0.0, 9.0)]) for _ in range(bids)])
    budgets = numpy.array([rng.uniform(0.0, 80.0) for _ in range(bids)])
    references = numpy.array([rng.uniform(1.0, 6.0) for _ in range(bids)])
    exponents = numpy.array([rng.uniform(0.0, 3.0) for _ in range(bids)])
    capped = rng.random() < 0.5
    maximums = numpy.array([rng.choice([numpy.inf, rng.uniform(1.0, 9.0)]) if capped else numpy.inf for _ in range(bids)])
    cuts = sorted(rng.sample(range(1, bids), rng.randint(0, min(2, bids - 1)))) if bids > 1 else []
    bounds = numpy.array([0] + cuts + [bids], dtype=numpy.int64)
    return asks, quantities, floors, flexibles, budgets, references, exponents, maximums, capped, bounds


def same(first, second):
    """Equal to the last bit, nan for nan (a tuple compares part by part)."""
    if isinstance(first, tuple):
        return len(first) == len(second) and all(same(each, other) for each, other in zip(first, second))
    return numpy.asarray(first).tobytes() == numpy.asarray(second).tobytes()


class EqualAskTests(unittest.TestCase):
    def test_choice_weights_match_the_plain_version(self):
        rng = random.Random(11)
        for _ in range(200):
            asks = numpy.array(sorted(rng.choice([0.0, 1.5, 1.5, 2.0, 3.25]) for _ in range(rng.randint(1, 12))))
            stocked = numpy.array([rng.random() < 0.7 for _ in asks])
            self.assertTrue(same(kernels.choice_weights(asks, stocked), plain.choice_weights(asks, stocked)))

    def test_requested_round_one_matches_the_plain_version(self):
        rng = random.Random(12)
        for _ in range(150):
            asks, quantities, *buyers, capped, _bounds = random_market(rng)
            self.assertTrue(same(kernels.requested_round_one(asks, quantities, *buyers, capped),
                                 plain.requested_round_one(asks, quantities, *buyers, capped)))

    def test_requested_round_one_ignores_a_dust_seller(self):
        buyer = (numpy.zeros(1), numpy.array([4.0]), numpy.array([1000.0]), numpy.array([2.0]), numpy.array([-1.0]), numpy.array([numpy.inf]), False)
        with_dust = kernels.requested_round_one(numpy.array([1.0, 2.0]), numpy.array([1e-12, 5.0]), *buyer)
        without = kernels.requested_round_one(numpy.array([2.0]), numpy.array([5.0]), *buyer)
        self.assertEqual(with_dust, without)

    def test_allocate_arrays_matches_the_plain_version(self):
        rng = random.Random(13)
        for _ in range(150):
            asks, quantities, floors, flexibles, budgets, references, exponents, maximums, capped, bounds = random_market(rng)
            arguments = (asks, quantities, floors, flexibles, budgets, references, exponents, maximums, capped, bounds)
            self.assertTrue(same(kernels.allocate_arrays(*arguments), plain.allocate_arrays(*arguments)))


if __name__ == "__main__":
    unittest.main()
