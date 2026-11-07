"""The opening's demand after the durable stock is seeded is asked of households holding that stock: the orders held for an
income from before the seed are dropped (`OwnPlots.forget_orders`, the held purse kept), orders dropped are made again
(`OwnPlots.resting_orders`), and the packed cohorts read the stock again (`OpeningDemand.repacked`). Each test calls one function."""

QUICK_TOPIC = True

import random
import unittest

from sim.economy import opening_demand, opening_demand_kernel as kernel
from sim.economy.opening_own import OwnPlots
from sim.tests.test_opening_demand_kernel import SPECS, parts_of, plots_of, random_world


class ForgetOrdersTests(unittest.TestCase):
    def test_the_orders_are_dropped_and_the_income_and_purse_kept(self):
        own = OwnPlots.__new__(OwnPlots)
        own.uncut = {"household:a:0": (100.0, "orders made before the seed", 7.0)}
        own.forget_orders()
        self.assertEqual(own.uncut, {"household:a:0": (100.0, None, 7.0)})


class RestingOrdersTests(unittest.TestCase):
    def ask(self, held):
        own = OwnPlots.__new__(OwnPlots)
        own.uncut, own.extra, own.in_kind = {"household:a:0": held}, {}, 0.0
        own._cut = lambda record, cohort, orders, basket, priced: (orders, 0.0)
        made = []
        cohort = type("Cohort", (), {"agent_id": "household:a:0"})()
        own.resting_orders(None, cohort, 100.0, None, None, lambda cash: made.append(cash) or "fresh orders")
        return made

    def test_orders_dropped_for_the_income_are_made_again_from_the_held_purse(self):
        self.assertEqual(self.ask((100.0, None, 0.0)), [100.0])

    def test_orders_held_for_the_income_and_purse_are_not_made_again(self):
        self.assertEqual(self.ask((100.0, "held orders", 0.0)), [])


class RepackedTests(unittest.TestCase):
    def test_the_stock_held_now_is_read_and_the_last_purse_kept(self):
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
