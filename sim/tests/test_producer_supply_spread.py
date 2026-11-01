"""The spread of workplace costs inside one producer follows from a short-run supply elasticity."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import producer_supply_spread


class SpreadForElasticityTest(unittest.TestCase):
    def test_half_working_unit_elasticity(self):
        # pdf(0) / (0.5 * 1.0) with pdf(0) = 1 / sqrt(2 pi)
        self.assertAlmostEqual(producer_supply_spread.spread_for_elasticity(1.0, 0.5), 0.7978845608, places=9)

    def test_share_one_sigma_above_the_median(self):
        # z = 1: pdf(1) = 0.2419707245, share = 0.8413447461, elasticity 0.5
        self.assertAlmostEqual(producer_supply_spread.spread_for_elasticity(0.5, 0.8413447461), 0.57520, places=5)

    def test_lower_elasticity_needs_wider_spread(self):
        wide = producer_supply_spread.spread_for_elasticity(0.2, 0.5)
        narrow = producer_supply_spread.spread_for_elasticity(2.0, 0.5)
        self.assertGreater(wide, narrow)


class SpreadAtBreakEvenTest(unittest.TestCase):
    def test_elasticity_at_revenue_equal_cost_is_the_target(self):
        for target in (0.1, 0.225, 1.0, 2.7):
            spread = producer_supply_spread.spread_at_break_even(target)
            score = spread / 2.0     # revenue equal to the mean cost sits half a spread above the median workplace
            density = math.exp(-score * score / 2.0) / math.sqrt(2.0 * math.pi)
            share = 0.5 * (1.0 + math.erf(score / math.sqrt(2.0)))
            self.assertAlmostEqual(density / (share * spread), target, places=6)

    def test_known_value(self):
        # the old declared spread of 0.3 has elasticity pdf(0.15) / (Phi(0.15) * 0.3) at break-even
        old = (math.exp(-0.15 ** 2 / 2.0) / math.sqrt(2.0 * math.pi)) / (0.5596177 * 0.3)
        self.assertAlmostEqual(producer_supply_spread.spread_at_break_even(old), 0.3, places=4)


if __name__ == "__main__":
    unittest.main()
