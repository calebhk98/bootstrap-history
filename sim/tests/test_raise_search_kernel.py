"""The sold-out raise evaluated with asks kept in order (`raise_search_kernel.search_covers`) against `goods_market_kernels.raise_search`,
which rebuilds the book at every step, and the price search's earnings (`price_setting_kernel.expected_earnings`) against the month
loop, on written-out and seeded random inputs."""
QUICK_TOPIC = True

import unittest

import numpy

from sim.economy import goods_market_kernels as kernels
from sim.economy import price_setting_kernel, raise_search_kernel

REPEATS = 400


def random_market(generator):
    """(reservations, quantities, raisable, limits, buyer arrays, minimum, has_minimum, capped) of a random sold-out market."""
    offers = int(generator.integers(1, 7))
    bids = int(generator.integers(1, 9))
    reservations = generator.choice([1.0, 1.0, 1.5, 2.0], offers) * generator.choice([1.0, 1.1], offers)
    quantities = generator.choice([0.0, 3.0, 8.0, 20.0], offers)
    raisable = generator.random(offers) < 0.7
    limits = numpy.where(generator.random(offers) < 0.5, numpy.inf, reservations * generator.choice([1.2, 2.0, 4.0], offers))
    floors = generator.choice([0.0, 0.5, 2.0], bids)
    flexibles = generator.choice([0.0, 4.0, 9.0], bids)
    budgets = generator.choice([0.0, 5.0, 40.0, 400.0], bids)
    references = generator.choice([1.0, 2.0], bids)
    exponents = -generator.choice([0.0, 0.5, 1.5], bids)
    capped = bool(generator.random() < 0.4)
    maximums = generator.choice([1.8, 3.0, 9.0], bids) if capped else numpy.full(bids, numpy.inf)
    has_minimum = bool(generator.random() < 0.4)
    return (reservations, quantities, raisable, limits, (floors, flexibles, budgets, references, exponents, maximums),
            float(generator.choice([0.0, 1.2])), has_minimum, capped)


class RaiseSearchTests(unittest.TestCase):
    def test_the_level_is_the_one_the_book_rebuilt_at_each_step_finds(self):
        generator = numpy.random.default_rng(5)
        found = 0
        for _case in range(REPEATS):
            reservations, quantities, raisable, limits, buyers, minimum, has_minimum, capped = random_market(generator)
            lowest = float(reservations.min())
            ceiling = lowest * float(generator.choice([1.5, 3.0, 8.0]))
            expected = kernels.raise_search(reservations, quantities, raisable, limits, lowest, ceiling, minimum, has_minimum,
                                            *buyers, capped)
            scratch = raise_search_kernel.make_scratch(len(reservations), len(buyers[0]))
            actual = raise_search_kernel.search_covers(reservations, quantities, float(quantities.sum()), raisable, limits, lowest,
                                                       ceiling, minimum, has_minimum, *buyers, capped, scratch)
            self.assertEqual(expected, actual)
            found += expected > 0.0
        self.assertGreater(found, 20)

    def test_nothing_lifted_covers_as_the_book_does(self):
        generator = numpy.random.default_rng(9)
        covered = 0
        for _case in range(REPEATS):
            reservations, quantities, raisable, limits, buyers, minimum, has_minimum, capped = random_market(generator)
            expected = kernels.covers_at(reservations, quantities, numpy.full(len(reservations), -1.0), minimum, has_minimum,
                                         *buyers, capped)
            scratch = raise_search_kernel.make_scratch(len(reservations), len(buyers[0]))
            actual = raise_search_kernel.covers_lifted(reservations, quantities, float(quantities.sum()), raisable, limits, -1.0,
                                                       minimum, has_minimum, *buyers, capped, scratch)
            self.assertEqual(expected, actual)
            covered += expected
        self.assertGreater(covered, 20)


class ExpectedEarningsTests(unittest.TestCase):
    def test_a_stock_that_covers_the_sales_earns_the_discounted_even_months(self):
        discounts = numpy.array([1.02 ** month for month in range(12)])
        annuity = float((1.0 / discounts).sum())
        earned = price_setting_kernel.expected_earnings(3.0, 1.0, 120.0, 500.0, 12, discounts, annuity)
        self.assertAlmostEqual(earned, 10.0 * 2.0 * annuity, places=12)

    def test_a_short_stock_is_sold_out_in_its_first_months(self):
        discounts = numpy.array([1.02 ** month for month in range(12)])
        annuity = float((1.0 / discounts).sum())
        earned = price_setting_kernel.expected_earnings(3.0, 1.0, 120.0, 25.0, 12, discounts, annuity)
        expected = (10.0 + 10.0 / 1.02 + 5.0 / 1.02 ** 2) * 2.0      # twenty-five units: ten, ten, five
        self.assertAlmostEqual(earned, expected, places=12)


if __name__ == "__main__":
    unittest.main()
