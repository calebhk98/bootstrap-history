"""Numba port, labour clearing: the hours a market's offers sell at a wage (`labour_supply_kernel.sold_hours`) agree with
the plain per-offer schedules (`HourSupply.sold_hours_schedule`) summed, on random offers and plots; no game.

The kernel sums left to right where the plain code used Python's compensated `sum`, so they agree to a relative tolerance."""

QUICK_TOPIC = True

import random
import unittest

from sim.economy import household_hours_year
from sim.economy.labour_supply import HourSupply
from sim.economy.types import LabourOffer

TOLERANCE = 1e-12     # a handful of ulps of a sum of a few terms


class SoldHoursKernelAgreesWithThePlainSchedules(unittest.TestCase):

    def test_parametric_plots(self):
        rng = random.Random(4)
        for _round in range(60):
            workers = ["w%d" % i for i in range(5)]
            offers = [LabourOffer(rng.choice(workers), "smith", "vale", rng.choice([0.0, rng.uniform(10, 900)]), 0.1)
                      for _ in range(rng.randint(1, 8))]
            plots = {worker: household_hours_year.plot_schedule(rng.uniform(100, 2000), rng.uniform(0.0, 3.0),
                                                                rng.uniform(0, 1500), rng.uniform(1, 30))
                     for worker in workers[:3]}
            supply = HourSupply(offers=offers, plan_hours={worker: rng.uniform(0, 300) for worker in workers[:2]},
                                work_hours={worker: rng.uniform(0, 300) for worker in workers[1:]}, plot_hours_at=plots)
            fast = supply.hours_at("smith", "vale")
            for wage in (-1.0, 0.0, 0.05, 0.7, 3.0, 50.0):
                plain = sum(supply.sold_hours_schedule(offer)(wage) for offer in offers if offer.hours > 0.0)
                self.assertAlmostEqual(fast(wage), plain, delta=TOLERANCE * max(1.0, abs(plain)))

    def test_a_plot_that_is_not_parametric_is_summed_in_python(self):
        offers = [LabourOffer("w0", "smith", "vale", 100.0, 0.1)]
        supply = HourSupply(offers=offers, plan_hours={}, work_hours={}, plot_hours_at={"w0": lambda wage: 40.0})
        self.assertEqual(supply.hours_at("smith", "vale")(1.0), 60.0)


if __name__ == "__main__":
    unittest.main()
