"""`python_sum`, `exact_sum` and `float_sumprod` give the numbers the built-ins `sum`, `math.fsum` and `math.sumprod` give, last digit included."""

QUICK_TOPIC = True

import math
import random
import unittest

import numpy

from sim.labour.market.exact_sums import exact_sum, float_sumprod, python_sum


def random_values(rng):
    count = rng.randint(1, 8)
    scale = 10.0 ** rng.randint(-8, 8)
    kind = rng.random()
    if kind < 0.3:
        return [rng.uniform(-1, 1) * scale for _ in range(count)]
    if kind < 0.6:
        return [rng.uniform(0, 1) * 10.0 ** rng.randint(-12, 12) for _ in range(count)]
    return [rng.choice([0.0, -0.0, 0.1, 0.2, 0.3, 1e16, -1e16, 1.0, rng.uniform(0, 5)]) for _ in range(count)]


class BuiltInSumsAreReproduced(unittest.TestCase):
    def test_python_sum_equals_sum_of_a_list(self):
        rng = random.Random(1)
        for _case in range(3000):
            values = random_values(rng)
            self.assertEqual(python_sum(numpy.array(values), len(values)), sum(values), values)

    def test_exact_sum_equals_fsum(self):
        rng = random.Random(2)
        for _case in range(3000):
            values = random_values(rng)
            self.assertEqual(exact_sum(numpy.array(values), len(values)), math.fsum(values), values)

    def test_float_sumprod_equals_math_sumprod(self):
        rng = random.Random(3)
        for _case in range(3000):
            count = rng.randint(1, 6)
            left = [rng.uniform(0, 1) * 10.0 ** rng.randint(-6, 6) for _ in range(count)]
            right = [rng.choice([0.0, 1.0, 0.5, rng.uniform(0, 1)]) for _ in range(count)]
            self.assertEqual(float_sumprod(numpy.array(left), numpy.array(right), count), math.sumprod(left, right), (left, right))

    def test_only_the_first_count_entries_are_added(self):
        values = numpy.array([0.1, 0.2, 0.3, 99.0])
        self.assertEqual((python_sum(values, 3), exact_sum(values, 3)), (sum([0.1, 0.2, 0.3]), math.fsum([0.1, 0.2, 0.3])))


if __name__ == "__main__":
    unittest.main()
