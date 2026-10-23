"""`CastView.need_floor_costs_per_person_year` and `subsistence_cost_per_person_year`: the strata's floor costs come from the
economy's tile prices when it has them, else from the goods market's need basket, else from the dole. Each is called on a
stand-in `self` carrying only what it reads."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.agents.api import DOLE_MATERIAL, FOOD_NEED
from sim.engine import agents_port_cast
from sim.engine.agents_port_cast import CastView


def stand_in(tile_costs, dole_cost=None):
    sim = types.SimpleNamespace(
        economy=types.SimpleNamespace(agent_need_floor_costs=lambda: tile_costs),
        civ={}, world_map=None,
        goods_market=types.SimpleNamespace(household_prices=lambda: {}))
    asked = []

    def material_cost(material, tonnes):
        asked.append((material, tonnes))
        return dole_cost
    return types.SimpleNamespace(_sim=sim, subsistence_kg_per_person_year=lambda: 250.0, material_cost=material_cost,
                                 asked=asked)


class NeedFloorCosts(unittest.TestCase):
    def test_the_economys_tile_costs_are_returned_as_they_are(self):
        tile_costs = {FOOD_NEED: 12.0, "shelter": 3.0}
        self.assertEqual(CastView.need_floor_costs_per_person_year(stand_in(tile_costs)), tile_costs)

    def test_with_no_tile_costs_and_no_priced_need_the_food_floor_is_the_dole(self):
        view = stand_in({}, dole_cost=9.0)
        with mock.patch.object(agents_port_cast.market_demand, "household_basket", return_value=[]), \
                mock.patch.object(agents_port_cast.need_basket, "need_prices", return_value=[]):
            costs = CastView.need_floor_costs_per_person_year(view)
        self.assertEqual(costs, {FOOD_NEED: 9.0})
        self.assertEqual(view.asked, [(DOLE_MATERIAL, 0.25)])

    def test_an_unpriced_dole_leaves_the_floor_empty(self):
        view = stand_in({}, dole_cost=None)
        with mock.patch.object(agents_port_cast.market_demand, "household_basket", return_value=[]), \
                mock.patch.object(agents_port_cast.need_basket, "need_prices", return_value=[]):
            self.assertEqual(CastView.need_floor_costs_per_person_year(view), {})


class SubsistenceCost(unittest.TestCase):
    def test_it_is_the_food_entry_of_the_floor_costs(self):
        view = types.SimpleNamespace(need_floor_costs_per_person_year=lambda: {FOOD_NEED: 12.0, "shelter": 3.0})
        self.assertEqual(CastView.subsistence_cost_per_person_year(view), 12.0)


if __name__ == "__main__":
    unittest.main()
