"""What a partner brings to the home society (sim/markets/goods_imports.py, import_tonnes_to_home)."""

QUICK_TOPIC = True

import unittest

from sim.markets.goods_imports import import_tonnes_to_home


class ImportTonnesToHomeTests(unittest.TestCase):
    def test_a_partners_tonnes_are_what_comes(self):
        self.assertEqual(import_tonnes_to_home(12.0), 12.0)

    def test_no_partner_selling_brings_none(self):
        self.assertEqual(import_tonnes_to_home(None), 0.0)

    def test_a_route_with_no_figure_brings_none(self):
        self.assertEqual(import_tonnes_to_home(float("inf")), 0.0)


if __name__ == "__main__":
    unittest.main()
