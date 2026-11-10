"""Numba port, labour switching: the year's discount tables (`switching_discounts.discount_tables`) hold what the plain
`premium.annuity_factor` and `expectations.present_value` give for each destination and kind of group; no game.

numba's `exp` and the math module's can differ in the last bit, so figures agree to a relative tolerance."""

QUICK_TOPIC = True

import math
import random
import unittest

import numpy as np

from sim.labour.market import expectations
from sim.labour.market.premium import annuity_factor
from sim.labour.market.switching_discounts import FULL, RETRAINED, YOUNG, career_gain, discount_tables

TOLERANCE = 1e-12


class TablesAgreeWithThePlainFormulas(unittest.TestCase):

    def test_random_years(self):
        rng = random.Random(4)
        for _case in range(200):
            rate = rng.choice([0.0, -0.01, rng.uniform(0.001, 0.2)])
            career, remaining_share, retraining = rng.uniform(5.0, 45.0), rng.uniform(0.2, 1.0), rng.uniform(0.1, 1.0)
            years = np.array([rng.choice([0.0, rng.uniform(0.5, 12.0), career * 1.2]) for _destination in range(rng.randint(1, 9))])
            tables = discount_tables(rate, career, remaining_share, years, retraining)
            kinds = {YOUNG: (1.0, career), FULL: (1.0, career * remaining_share), RETRAINED: (retraining, career * remaining_share)}
            for kind, (share, remaining) in kinds.items():
                for destination, training in enumerate(years.tolist()):
                    trained = training * share
                    self.assertAlmostEqual(tables.lost[kind, destination], annuity_factor(rate, trained), delta=TOLERANCE * (1.0 + trained))
                    self.assertEqual(bool(tables.pays[kind, destination]), remaining > trained)
                    amount = rng.uniform(-3.0, 9.0)
                    got = career_gain(amount, tables.start[kind, destination], tables.after[kind, destination], tables.pays[kind, destination])
                    want = expectations.present_value(amount, rate, trained, remaining)
                    self.assertAlmostEqual(got, want, delta=TOLERANCE * (1.0 + abs(want)))


if __name__ == "__main__":
    unittest.main()
