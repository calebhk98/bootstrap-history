"""A provider's deaths reach the population step: the year's epidemic deaths handed to the step add what the externality providers
say, band by band. The demography view `externality_deaths` answers through the module's own point. The arithmetic is test_externalities; the yield factor reaching land-bound
producers is test_externality_pooled_harvest. Stand-ins carry only what each function reads."""
QUICK_TOPIC = True

import unittest

from sim.demography.module import Demography
from sim.tests import module_harness


class ExternalityDeathsTests(unittest.TestCase):
    def test_the_demography_view_asks_the_point_with_the_game_and_the_year(self):
        asked = []
        module = module_harness.build(Demography, views={
            "legacy_game": "the game", "externality": lambda game, year: asked.append((game, year)) or [{"deaths_by_band": {"children": 7.0}}]})
        self.assertEqual(module.externality_deaths({"children": 1.0}, 1300), {"children": 8.0})
        self.assertEqual(asked, [("the game", 1300)])


if __name__ == "__main__":
    unittest.main()
