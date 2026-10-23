"""allowed_entries: a society that holds no draught-animal capability is offered no recipe that holds a draught team."""

QUICK_TOPIC = True

import unittest

from sim.economy.recipes import recipes_from_production_data
from sim.engine.economy_port_setup import allowed_entries
from sim.world import demand


class AllowedWithoutDraught(unittest.TestCase):

    def test_no_allowed_recipe_holds_a_draught_team_as_plant(self):
        production = demand.production_data()
        recipes = recipes_from_production_data(production)
        allowed = allowed_entries(production, set())
        self.assertIn("wheat_hoe_kg", allowed)
        holding_a_team = sorted(key for key in allowed if "draught_animal_kg" in recipes[key].plant_goods)
        self.assertEqual(holding_a_team, [])


if __name__ == "__main__":
    unittest.main()
