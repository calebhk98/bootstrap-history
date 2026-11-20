"""Numba port, labour clearing: the small helper of the hiring rounds (`hiring_kernel._first_below`) gives what a count over
the ranked posters gives; no game."""

QUICK_TOPIC = True

import random
import unittest

import numpy as np

from sim.labour.market import hiring_kernel


class PostersReached(unittest.TestCase):

    def test_equals_a_count_of_offers_at_the_ask(self):
        rng = random.Random(6)
        for _case in range(500):
            count = rng.randint(0, 12)
            offers = np.array([rng.choice([1.0, 1.5, 2.0, 3.0, rng.uniform(0.5, 4.0)]) for _poster in range(count + 2)])
            ranked = np.array(sorted(range(count + 2), key=lambda poster: -offers[poster]), np.int64)
            ask = rng.choice([0.4, 1.0, 1.5, 2.0, 3.0, 5.0, rng.uniform(0.5, 4.0)])
            self.assertEqual(hiring_kernel._first_below(ranked, count, offers, ask), sum(1 for poster in ranked[:count] if offers[poster] >= ask))


if __name__ == "__main__":
    unittest.main()
