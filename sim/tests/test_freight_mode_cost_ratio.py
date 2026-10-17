"""Complaints/541: physical freight cost per tonne-km, by mode, keeps the order and rough proportions of
the Edict of Diocletian's grain rates (about 1 sea : 5 river : 28-40 land by wagon).

A relationship check under CLAUDE.md 4.2, not a tuning target. The bands are wide on purpose: the Edict is
one source (maximum prices, so margins, risk, tolls and port dues sit in its sea and river figures, and
the land figure is a wagon on a road), while this measures only labour hours with feed converted, from the
same rates the route search uses (`routes_rates`). Edict land rates are for a road, so the comparison is
the built road; carts on unbuilt track and pack strings are checked only for order against it.
"""

QUICK_TOPIC = True

import unittest

from sim.geography import map_source, routes_rates

FLAT = 0.0
GENTLE = 0.02            # the grade the complaint's measurement uses
UPSTREAM_KM_PER_HOUR = -1.0
SEA_TO_RIVER_BAND = (2.0, 8.0)       # Edict about 5; still water to a fair current against the boat
SEA_TO_ROAD_BAND = (10.0, 60.0)      # Edict 28-40; flat road up to a gentle grade
ROAD_TO_UNBUILT_BAND = (1.5, 6.0)    # a team on dirt track against the same team on paving


class FreightModeCostRatio(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.world_map = map_source.load_map()
        cls.table = routes_rates.rate_table(cls.world_map)

    def cost(self, mode, edge_class, grade, current=0.0):
        rate = self.table.rate(mode, edge_class, grade, current)
        self.assertIsNotNone(rate, (mode, edge_class, grade, current))
        return routes_rates.physical_cost(self.world_map, rate)

    def ratio(self, mode, edge_class, grade, current=0.0):
        return self.cost(mode, edge_class, grade, current) / self.cost("sail", "coast", grade)

    def test_river_costs_a_few_times_the_sea(self):
        low, high = SEA_TO_RIVER_BAND
        for grade, current in ((FLAT, 0.0), (GENTLE, 0.0), (FLAT, UPSTREAM_KM_PER_HOUR)):
            self.assertTrue(low <= self.ratio("river_boat", "river", grade, current) <= high, (grade, current))

    def test_a_built_road_costs_tens_of_times_the_sea(self):
        low, high = SEA_TO_ROAD_BAND
        for grade in (FLAT, GENTLE):
            self.assertTrue(low <= self.ratio("road", "land", grade) <= high, grade)

    def test_unbuilt_land_carriage_costs_more_than_a_road(self):
        low, high = ROAD_TO_UNBUILT_BAND
        for grade in (FLAT, GENTLE):
            road = self.cost("road", "land", grade)
            self.assertTrue(low <= self.cost("cart", "land", grade) / road <= high, grade)
            self.assertGreater(self.cost("pack", "land", grade), self.cost("cart", "land", grade))

    def test_modes_order_sea_river_road_cart(self):
        for grade in (FLAT, GENTLE):
            costs = [self.cost(*mode, grade) for mode in
                     (("sail", "coast"), ("river_boat", "river"), ("road", "land"), ("cart", "land"))]
            self.assertEqual(costs, sorted(costs))


if __name__ == "__main__":
    unittest.main()
