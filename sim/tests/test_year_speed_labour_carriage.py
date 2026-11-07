"""Numba port, labour: `carriage.carriage_table` (every origin's cheapest moving cost in one search over arrays) agrees with
`carriage.carriage_from` (one heap search per origin) on random route graphs; no game.

The two add the costs of a path in another order, so the totals agree to a relative tolerance."""

QUICK_TOPIC = True

import random
import unittest

from sim.labour.market import carriage
from sim.labour.market.records import Route

TOLERANCE = 1e-12


class CarriageTableAgreesWithOneSearchPerOrigin(unittest.TestCase):

    def test_random_graphs(self):
        rng = random.Random(3)
        for _case in range(100):
            names = ["a%02d" % index for index in range(rng.randint(1, 14))]
            routes = {}
            for origin in names:
                if rng.random() < 0.8:
                    routes[origin] = [Route(rng.choice(names), rng.choice([-5.0, 0.0, rng.uniform(0.0, 100.0)]))
                                      for _way in range(rng.randint(0, 4))]
            table = carriage.carriage_table(routes)
            for origin in names:
                expected = carriage.carriage_from(routes, origin)
                got = table.get(origin, {origin: 0.0})
                self.assertEqual(sorted(got), sorted(expected))
                for area, cost in expected.items():
                    self.assertAlmostEqual(got[area], cost, delta=TOLERANCE * max(1.0, abs(cost)))

    def test_no_routes(self):
        self.assertEqual(carriage.carriage_table({}), {})


if __name__ == "__main__":
    unittest.main()
