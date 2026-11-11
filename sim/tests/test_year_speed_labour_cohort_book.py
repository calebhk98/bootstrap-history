"""Numba port, labour switching: the people a market has in training (`cohort_book.enrolled`) and the graduates it expects
(`graduates_coming`) equal the `math.fsum` of each cohort's `math.fsum` and `math.sumprod`, for a market with none, one or
several cohorts, in the state's table or pending; no game."""

QUICK_TOPIC = True

import math
import random
import unittest

import numpy as np

from sim.labour.market import cohort_book


def book_with(rng, bands, in_state, pending):
    """A book of one market (row 0) with `in_state` cohorts in the state's table and `pending` new ones; their people per band."""
    people = np.array([[rng.uniform(0.0, 40.0) for _band in range(bands)] for _cohort in range(max(in_state, 1))])
    book = cohort_book.CohortBook(np.zeros(1, np.int64), np.array([in_state], np.int64), np.zeros(max(in_state, 1)), np.zeros(max(in_state, 1)),
                                  people, cohort_book.PENDING.new_table(cohort_book.Pending, 8, widths={"people": bands}),
                                  np.full(1, -1, np.int64), np.full(1, -1, np.int64), np.zeros(1, np.int64))
    added = [np.array([rng.uniform(0.0, 40.0) for _band in range(bands)]) for _cohort in range(pending)]
    for bands_added in added:
        cohort_book.add_cohort(book, 0, 2.0, 0.0, bands_added)
    return book, [row.tolist() for row in people[:in_state]] + [row.tolist() for row in added]


class CohortSums(unittest.TestCase):

    def test_enrolled_and_graduates_coming(self):
        rng = random.Random(12)
        for _case in range(200):
            bands = rng.randint(1, 5)
            book, cohorts = book_with(rng, bands, rng.randint(0, 3), rng.randint(0, 3))
            chances = np.array([rng.uniform(0.0, 1.0) for _band in range(bands)])
            self.assertEqual(cohort_book.enrolled(book, 0), math.fsum(math.fsum(row) for row in cohorts))
            self.assertEqual(cohort_book.graduates_coming(book, 0, chances), math.fsum(math.sumprod(row, chances.tolist()) for row in cohorts))


if __name__ == "__main__":
    unittest.main()
