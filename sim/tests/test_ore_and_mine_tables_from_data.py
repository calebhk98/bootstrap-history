"""Complaint 441: the ore, metal and mine tables are catalogue data, so a mod adds a mineral without engine
edits. On shipped data the derived tables equal the literals the engine used to carry."""

QUICK_TOPIC = True

import json
import os
import tempfile
import unittest

from sim.geography import api as geography_api
from sim.world import deposits

OLD_METALS = ("iron", "copper", "tin", "lead", "silver", "gold", "mercury")
OLD_RENT_BEARING_ORE_MATERIALS = {
    "iron_ore_kg": ("iron", ("pig_iron_kg", "iron_bloom_kg")),
    "copper_ore_kg": ("copper", ("copper_kg",)),
    "cassiterite_kg": ("tin", ("tin_kg",)),
    "galena_kg": ("lead", ("lead_kg",)),
    "silver_ore_kg": ("silver", ("silver_kg",)),
    "cinnabar_kg": ("mercury", ("mercury_kg",)),
    "gold_gravel_kg": ("gold", ("gold_kg",)),
    "gold_lode_ore_kg": ("gold", ("gold_lode_kg",)),
}
OLD_MINE_OPEX_MATERIALS = {"coal", "iron", "copper", "lead", "tin", "silver", "gold"}


class OreTablesFromDataTests(unittest.TestCase):
    def test_the_metals_equal_the_old_literal(self):
        self.assertEqual(deposits.metals(), OLD_METALS)
        self.assertEqual(deposits.METALS, OLD_METALS)

    def test_the_rent_bearing_ores_equal_the_old_literal(self):
        self.assertEqual(deposits.rent_bearing_ore_materials(), OLD_RENT_BEARING_ORE_MATERIALS)

    def test_the_materials_priced_from_their_works_equal_the_old_literal(self):
        self.assertEqual(set(geography_api.works_priced_from_deposits()), OLD_MINE_OPEX_MATERIALS)

    def test_the_mining_trade_is_a_map_parameter(self):
        self.assertEqual(geography_api.parameter_value("mining_trade"), "miner")

    def test_the_engine_no_longer_carries_the_tables(self):
        from sim.engine import solve_prices, solve_prices_core
        self.assertFalse(hasattr(solve_prices_core, "RENT_BEARING_ORE_MATERIALS"))
        self.assertFalse(hasattr(solve_prices, "RENT_BEARING_ORE_MATERIALS"))

    def test_a_mod_adds_an_ore_without_engine_edits(self):
        with tempfile.TemporaryDirectory() as mods_dir:
            root = os.path.join(mods_dir, "ore_add_p4w2")
            folder = os.path.join(root, "data", "world", "geography", "resources")
            os.makedirs(folder)
            with open(os.path.join(root, "mod.json"), "w", encoding="utf-8") as handle:
                json.dump({"id": "ore_add_p4w2", "name": "Ore add", "version": "1.0.0", "dependencies": [],
                           "conflicts": []}, handle)
            with open(os.path.join(folder, "zinc.json"), "w", encoding="utf-8") as handle:
                json.dump({"entries": [{
                    "id": "ore_add_p4w2:zinc_test", "mechanism": "mineral_deposit", "unit": "kg",
                    "ore_goods": {"calamine_kg": ["zinc_kg"]}, "works_priced_from_deposits": True,
                    "deposit_types": [{"id": "zinc_vein_test", "deposits_per_million_km2": 1,
                                       "tonnage_lognormal": {"median_tonnes": 1000.0, "sigma": 1.0},
                                       "depth_class": "shallow_vein", "grade_lognormal": {"median_kg_per_tonne": 0.05, "sigma": 0.5},
                                       "source": "test", "conf": "D"}]}]}, handle)
            modded = geography_api.open_map([("ore_add_p4w2", root)])
            self.assertIn("ore_add_p4w2:zinc_test", deposits.metals(modded))
            self.assertEqual(deposits.rent_bearing_ore_materials(modded)["calamine_kg"], ("ore_add_p4w2:zinc_test", ("zinc_kg",)))
            self.assertIn("ore_add_p4w2:zinc_test", geography_api.works_priced_from_deposits(modded))
        self.assertNotIn("ore_add_p4w2:zinc_test", deposits.metals())


if __name__ == "__main__":
    unittest.main()
