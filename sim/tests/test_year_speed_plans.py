"""Numba port, the producers' yearly plans: `plan_year.plans_of` (one kernel over the year arrays, `plan_kernel.plan_rows`)
gives each producer the plan `producers.plan` gives it: runs, runs wanted, wage line, labour bids and input bids. Random
economies of year_close_fixture (stocks, cash, expectations, land caps, idle producers, joint outputs), no game.

A relative tolerance is needed because the kernel adds a bill left to right where the dictionaries add in the order the
recipe lists them and `math.fsum` sums exactly. Most plans must be compared and some must run."""

QUICK_TOPIC = True

import math
import unittest
from dataclasses import replace

from sim.economy import plan_year, producers
from sim.economy.year_arrays import YearArrays
from sim.economy.year_arrays_costs import refreshed
from sim.tests.year_close_fixture import MONEY, economy_of

RELATIVE = 1e-8


def near(left, right):
    if math.isinf(left) or math.isinf(right):
        return left == right
    return abs(left - right) <= RELATIVE * max(abs(left), abs(right), 1e-12)


class PlansAreThePlainPlans(unittest.TestCase):

    def test_every_producer_of_random_economies(self):
        compared = running = 0
        for seed in range(8):
            setup, record, view, _ledger, area_map = economy_of(seed, producer_count=60)
            for producer_id in sorted(record.producers)[::7]:      # some idle after a bankruptcy
                record.producers[producer_id] = replace(record.producers[producer_id], idle_years=2)
            arrays = refreshed(YearArrays.build(setup, record, area_map, view), setup, record, view)
            plans = plan_year.plans_of(setup, record, view, arrays, MONEY)
            self.assertEqual(list(plans.ids), sorted(record.producers))
            for producer_id in plans.ids:
                found = plans.plan_of(producer_id)
                producer = record.producers[producer_id]
                plain = producers.plan(producer, setup.recipes[producer.recipe_id], view, record.book.balance(producer_id, MONEY))
                compared += 1
                running += plain.runs > 0.0
                for field in ("runs", "wanted_runs", "wage_line"):
                    self.assertTrue(near(getattr(found, field), getattr(plain, field)), (producer_id, field, found, plain))
                self.assertEqual(len(found.labour_bids), len(plain.labour_bids))
                self.assertEqual(len(found.bids), len(plain.bids))
                for mine, theirs in zip(found.labour_bids, plain.labour_bids):
                    self.assertEqual((mine.employer, mine.trade, mine.area), (theirs.employer, theirs.trade, theirs.area))
                    self.assertTrue(near(mine.hours, theirs.hours) and near(mine.maximum_wage, theirs.maximum_wage))
                for mine, theirs in zip(found.bids, plain.bids):
                    self.assertEqual((mine.buyer, mine.good, mine.area, mine.tile), (theirs.buyer, theirs.good, theirs.area, theirs.tile))
                    for field in ("floor_quantity", "reference_price", "budget", "maximum_price"):
                        self.assertTrue(near(getattr(mine, field), getattr(theirs, field)), (producer_id, field))
        self.assertGreater(compared, 300)
        self.assertGreater(running, 50)


if __name__ == "__main__":
    unittest.main()
