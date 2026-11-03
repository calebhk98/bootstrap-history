"""The markets port weighs a unit of a good by the economy's one mass rule (sim/economy/good_mass.py)."""
QUICK_TOPIC = True

import unittest

from sim.markets.unit_mass import tonnes_per_unit


class TonnesPerUnit(unittest.TestCase):

    def test_a_unit_counted_in_tonnes_weighs_a_tonne(self):
        self.assertEqual(tonnes_per_unit("stone_tons"), 1.0)

    def test_a_stated_mass_beats_a_kilogram_a_unit(self):
        self.assertEqual(tonnes_per_unit("brick_1000"), 2.5)

    def test_a_unit_in_grams_weighs_a_gram(self):
        self.assertAlmostEqual(tonnes_per_unit("gold_g"), 1.0e-6)

    def test_a_unit_that_is_not_a_mass_has_no_tonnes(self):
        self.assertIsNone(tonnes_per_unit("hectare_of_land"))
