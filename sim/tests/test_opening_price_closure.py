"""Opening prices are a closed set: a good is priced only when it can be made at that start (Complaint 566)."""

import os
import unittest

from sim.engine.economy_port_setup import build_setup
from sim.tests.harness import unopened_sim
from sim.world import demand

CIVILISATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                 "data", "civilizations")


def _civilisation_ids():
    return sorted(name[:-5] for name in os.listdir(CIVILISATIONS_DIR) if name.endswith(".json") and not name.startswith("_"))


class OpeningPriceClosureTests(unittest.TestCase):
    def test_england_has_no_price_for_lamps_it_cannot_make(self):
        prices = build_setup(unopened_sim(civ="england_1300")).opening_prices
        self.assertNotIn("light_oil_lamp", prices)       # its oil is not supplied
        self.assertNotIn("light_electric_lamp", prices)  # its node is not held

    def test_rome_still_prices_its_oil_lamp(self):
        self.assertGreater(build_setup(unopened_sim(civ="rome_100ad")).opening_prices["light_oil_lamp"], 0.0)

    def test_every_priced_good_has_a_runnable_recipe_with_priced_inputs(self):
        production = demand.production_data()
        makers_anywhere = {good for entry_id, entry in production.items()
                           if not entry_id.startswith("_") and isinstance(entry, dict)
                           for good in (entry.get("outputs") or {})}
        for civilisation_id in _civilisation_ids():
            with self.subTest(civilisation=civilisation_id):
                setup = build_setup(unopened_sim(civ=civilisation_id))
                prices = setup.opening_prices
                for good in prices:
                    if good not in makers_anywhere:
                        continue
                    self.assertTrue(any(
                        good in recipe.outputs and all(item in prices for item in recipe.inputs)
                        and production[recipe.recipe_id].get("requires_node") in (None, *setup.held_nodes)
                        for recipe in setup.recipes.values()), (civilisation_id, good))


if __name__ == "__main__":
    unittest.main()
