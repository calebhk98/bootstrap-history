"""BASELINE VALIDATION (CLAUDE.md 4.2): the money freight ratios of a Rome opening against the Edict of Diocletian.

Complaints/541: the money rate per tonne-km by mode (feed, crew, carrier capital, hull loss, return leg),
as a Rome opening's freight function charges it, keeps the order and rough proportions of the Edict of
Diocletian's grain rates (about 1 sea : 5 river : 28-40 land by wagon).

A relationship check under CLAUDE.md 4.2, not a tuning target. The bands are wide because the Edict is one
source of maximum prices (margins, risk and dues sit in its sea and river figures; its land figure is a wagon
on a road) and because the model's still-water river has no current or windings (see the complaint). The
physical sibling check is `test_freight_mode_cost_ratio`.
"""

QUICK_TOPIC = False

import unittest

from sim.tests.harness import unopened_sim

RIVER_OVER_SEA_BAND = (1.5, 8.0)     # Edict about 5
ROAD_OVER_SEA_BAND = (5.0, 60.0)     # Edict 28-40
UNBUILT_OVER_ROAD_BAND = (1.5, 6.0)  # a team on dirt track against the same team on paving
ONE_SIDED = 1.0
BALANCED = 0.0


class FreightMoneyRatio(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        game = unopened_sim()
        cls.costs = {imbalance: game._freight_mode_costs(imbalance) for imbalance in (ONE_SIDED, BALANCED)}

    def ratio(self, mode, imbalance):
        return self.costs[imbalance][mode] / self.costs[imbalance]["sail"]

    def test_river_costs_a_few_times_the_sea(self):
        low, high = RIVER_OVER_SEA_BAND
        for imbalance in self.costs:
            self.assertTrue(low <= self.ratio("river_boat", imbalance) <= high, imbalance)

    def test_a_built_road_costs_tens_of_times_the_sea(self):
        low, high = ROAD_OVER_SEA_BAND
        for imbalance in self.costs:
            self.assertTrue(low <= self.ratio("road", imbalance) <= high, imbalance)

    def test_unbuilt_land_carriage_costs_more_than_a_road(self):
        low, high = UNBUILT_OVER_ROAD_BAND
        for imbalance, costs in self.costs.items():
            self.assertTrue(low <= costs["cart"] / costs["road"] <= high, imbalance)
            self.assertGreater(costs["pack"], costs["cart"])

    def test_modes_order_sea_river_road_cart_pack(self):
        for costs in self.costs.values():
            ordered = [costs[mode] for mode in ("sail", "river_boat", "road", "cart", "pack")]
            self.assertEqual(ordered, sorted(ordered))


if __name__ == "__main__":
    unittest.main()
