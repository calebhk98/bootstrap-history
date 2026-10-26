"""The price rules of a bought material (sim/freight/rules.py, sim/materials/rules.py): the freight markup on the book price and
the scarcity factor from how hard demand leans on the supply. Complaint 640: rules on inputs built here, no game."""
import unittest

from sim.materials.rules import scarcity_factor
from sim.freight.rules import freight_markup

QUICK_TOPIC = True


class FreightMarkup(unittest.TestCase):

    def test_a_haul_adds_its_cost_per_kilogram_over_the_price(self):
        self.assertAlmostEqual(freight_markup(2.0, 1000.0, 0.0), 1.5)

    def test_the_cargos_own_cost_share_adds_on(self):
        self.assertAlmostEqual(freight_markup(2.0, 1000.0, 0.1), 1.6)

    def test_no_haul_is_no_markup(self):
        self.assertEqual(freight_markup(2.0, 0.0, 0.1), 1.0)
        self.assertEqual(freight_markup(2.0, None, 0.1), 1.0)

    def test_a_material_without_a_price_is_left_alone(self):
        self.assertEqual(freight_markup(0.0, 1000.0, 0.1), 1.0)
        self.assertEqual(freight_markup(None, 1000.0, 0.1), 1.0)

    def test_a_dearer_haul_is_a_bigger_markup(self):
        self.assertGreater(freight_markup(2.0, 3000.0, 0.0), freight_markup(2.0, 1000.0, 0.0))


class ScarcityFactor(unittest.TestCase):

    def test_nothing_needed_is_no_pressure(self):
        self.assertEqual(scarcity_factor([], 10.0, 1.5, 0.9), 1.0)
        self.assertEqual(scarcity_factor([(0.0, 0.0)], 10.0, 1.5, 0.9), 1.0)

    def test_pressure_is_scale_times_the_share_squared(self):
        self.assertAlmostEqual(scarcity_factor([(5.0, 0.0)], 10.0, 1.5, 0.9), 1.0 + 0.9 * 0.25)

    def test_the_share_is_capped(self):
        self.assertAlmostEqual(scarcity_factor([(1000.0, 0.0)], 10.0, 1.5, 0.9), 1.0 + 0.9 * 1.5 * 1.5)

    def test_own_supply_removes_pressure(self):
        self.assertLess(scarcity_factor([(5.0, 100.0)], 10.0, 1.5, 0.9), scarcity_factor([(5.0, 0.0)], 10.0, 1.5, 0.9))

    def test_the_dearest_demand_decides(self):
        both = scarcity_factor([(2.0, 0.0), (8.0, 0.0)], 10.0, 1.5, 0.9)
        self.assertAlmostEqual(both, scarcity_factor([(8.0, 0.0)], 10.0, 1.5, 0.9))

    def test_no_supply_does_not_divide_by_zero(self):
        self.assertAlmostEqual(scarcity_factor([(1.0, 0.0)], 0.0, 1.5, 0.9), 1.0 + 0.9 * 1.5 * 1.5)


if __name__ == "__main__":
    unittest.main()
