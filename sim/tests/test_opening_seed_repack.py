"""The opening's demand after the durable stock is seeded is asked of households holding that stock: the packed cohorts read the
stock again (`OpeningDemand.repacked`). Each test calls one function."""

QUICK_TOPIC = True

import random
import unittest

from sim.economy import opening_demand, opening_demand_kernel as kernel
from sim.tests.test_opening_demand_kernel import SPECS, parts_of, plots_of, random_world


class RepackedTests(unittest.TestCase):
    def test_the_stock_held_now_is_read_and_the_last_incomes_kept(self):
        rng = random.Random(4)
        basket, view, cohorts = random_world(rng)
        packed = opening_demand.OpeningDemand(parts_of(basket, view, cohorts), view, SPECS, plots_of({}))
        packed.memo[:] = 3.0
        view.held[(packed.cohorts[0].agent_id, "hoe")] = 5.0
        fresh = packed.repacked()
        hoe = fresh.goods.index("hoe")
        rows = [row for row in range(fresh.cohort_ints[0, kernel.CI_ROW0], fresh.cohort_ints[0, kernel.CI_ROW1])
                if fresh.row_ints[row, kernel.RI_GOOD] == hoe]
        self.assertTrue(rows)
        self.assertEqual([fresh.row_floats[row, kernel.RF_HELD] for row in rows], [5.0] * len(rows))
        self.assertEqual(fresh.memo.tolist(), packed.memo.tolist())


if __name__ == "__main__":
    unittest.main()
