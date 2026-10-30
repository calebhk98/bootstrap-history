"""A mortality shock's wage premium is logged for the player: the demography module's `refresh_demographic_indexes`, reading the wage
index and its terms as views and sending the reporting event."""
QUICK_TOPIC = True

import unittest

from sim.demography.api import RefreshDemographicIndexes
from sim.demography.module import Demography
from sim.demography.state import DemographyWorld
from sim.reporting.api import RecordEvent
from sim.tests import module_harness


def built(wage_index, said=-1000, base=1.0, elasticity=0.5):
    return module_harness.build(Demography, views={"wage_index": wage_index, "wage_index_terms": {"base": base, "elasticity": elasticity}},
                                world=DemographyWorld(said_wage_cascade=said))


class WageCascadeLog(unittest.TestCase):
    def test_a_premium_is_logged_with_its_size_and_the_shortfall_behind_it(self):
        module = built(wage_index=1.5)
        module.refresh_demographic_indexes(RefreshDemographicIndexes(1348))
        (event,) = module_harness.sent(module)
        self.assertIsInstance(event, RecordEvent)
        self.assertEqual((event.year, event.kind), (1348, "wage_cascade"))
        self.assertEqual(event.facts, {"population_below_trend_percent": 100, "wage_premium_percent": 50})
        self.assertEqual(module.world.said_wage_cascade, 1348)

    def test_a_premium_under_half_a_percent_is_not_logged(self):
        module = built(wage_index=1.004)
        module.refresh_demographic_indexes(RefreshDemographicIndexes(1348))
        self.assertEqual(module_harness.sent(module), [])

    def test_it_is_not_repeated_within_the_spacing(self):
        module = built(wage_index=1.5, said=1340)
        module.refresh_demographic_indexes(RefreshDemographicIndexes(1348))
        self.assertEqual(module_harness.sent(module), [])
        module.refresh_demographic_indexes(RefreshDemographicIndexes(1355))
        self.assertEqual(len(module_harness.sent(module)), 1)


if __name__ == "__main__":
    unittest.main()
