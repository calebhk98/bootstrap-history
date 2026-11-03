"""The hands a tile has left beyond its producers' hiring are counted at the hours a working person of the tile's labour area
was seeded to sell, as the workforce settling counts them. `hands_left_by_tile` is called on stand-ins; the producers' hiring is
patched to nothing so only the hours per worker differ."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.economy import opening_plans
from sim.economy.labour_record import LabourRecord
from sim.economy.setup import labour_area


def setup():
    return types.SimpleNamespace(working_hours_per_year=2000.0, working_share=0.5,
                                 opening_population_by_tile={"north": 100.0, "south": 100.0})


class HandsLeft(unittest.TestCase):
    def hands(self, **seeded):
        record = types.SimpleNamespace(labour=LabourRecord(**seeded))
        with mock.patch.object(opening_plans.labour_state, "producers_hours_needed", return_value={}):
            return opening_plans.hands_left_by_tile(setup(), record)

    def test_each_tile_is_counted_at_the_hours_its_area_was_seeded_to_sell(self):
        hands = self.hands(opening_sold_hours_by_area={labour_area("north"): 1000.0, labour_area("south"): 500.0})
        self.assertEqual(hands, {"north": 100.0 * 0.5 * 1000.0, "south": 100.0 * 0.5 * 500.0})

    def test_without_a_figure_per_area_the_one_figure_and_then_a_working_year_stand(self):
        self.assertEqual(self.hands(opening_sold_hours_per_worker=800.0), {"north": 40000.0, "south": 40000.0})
        self.assertEqual(self.hands(), {"north": 100000.0, "south": 100000.0})


if __name__ == "__main__":
    unittest.main()
