"""Complaint 534: lime can be burned with firewood as well as coal, and Roman hydraulic concrete (lime plus
pozzolana plus rubble aggregate) exists, with pozzolana occurring only in the volcanic districts it is sourced to."""

QUICK_TOPIC = True

import math
import unittest

from sim.engine.validate_production import load_production
from sim.geography import api as geography_api

CALCIUM_CARBONATE_MOLAR_MASS = 100.09
CALCIUM_OXIDE_MOLAR_MASS = 56.08
CALCIUM_HYDROXIDE_MOLAR_MASS = 74.09
CALCINATION_ENTHALPY_MJ_PER_KG_LIMESTONE = 1.78
SENSIBLE_HEAT_MJ_PER_KG_LIME = 1.4
FIREWOOD_MJ_PER_KG = 15.0
KILOMETRES_PER_DEGREE = 111.0

# Volcanic districts the pozzolana entry is sourced to: (latitude, longitude) of the district centre.
VOLCANIC_DISTRICT_CENTRES = {
    "Campi Flegrei and Vesuvius": (40.83, 14.20),
    "Alban Hills": (41.75, 12.70),
    "Santorini": (36.40, 25.40),
    "Eifel": (50.40, 7.30),
}
DISTRICT_RADIUS_KM = 60.0


def distance_km(first, second):
    mean_latitude = math.radians((first[0] + second[0]) / 2.0)
    north = (first[0] - second[0]) * KILOMETRES_PER_DEGREE
    east = (first[1] - second[1]) * KILOMETRES_PER_DEGREE * math.cos(mean_latitude)
    return math.hypot(north, east)


class WoodFiredLimeTests(unittest.TestCase):

    def setUp(self):
        self.production = load_production()[0]

    def test_a_wood_fired_lime_recipe_exists_beside_the_coal_one(self):
        wood = self.production["lime_wood_kg"]
        self.assertEqual(list(wood["outputs"]), ["lime_kg"])
        self.assertIn("firewood_kg", wood["inputs"])
        self.assertNotIn("coal_kg", wood["inputs"])
        self.assertIn("coal_kg", self.production["lime_kg"]["inputs"])

    def test_it_balances_mass_and_heat(self):
        wood = self.production["lime_wood_kg"]
        lime_kg = wood["outputs"]["lime_kg"]
        minimum_limestone_kg = lime_kg * CALCIUM_CARBONATE_MOLAR_MASS / CALCIUM_OXIDE_MOLAR_MASS
        self.assertGreaterEqual(wood["inputs"]["limestone_kg"], minimum_limestone_kg)
        self.assertLessEqual(wood["inputs"]["limestone_kg"], 1.1 * minimum_limestone_kg)
        required_mj = (minimum_limestone_kg * CALCINATION_ENTHALPY_MJ_PER_KG_LIMESTONE
                       + lime_kg * SENSIBLE_HEAT_MJ_PER_KG_LIME)
        supplied_mj = wood["inputs"]["firewood_kg"] * FIREWOOD_MJ_PER_KG
        kiln_efficiency = required_mj / supplied_mj
        self.assertGreater(kiln_efficiency, 0.10)
        self.assertLess(kiln_efficiency, 0.40)

    def test_it_states_its_source(self):
        wood = self.production["lime_wood_kg"]
        self.assertIn("requires_node", wood)
        self.assertGreater(len(wood["yield_basis"]), 200)
        self.assertEqual(wood["unit_dimension"], "mass")


class PozzolanicConcreteTests(unittest.TestCase):

    def setUp(self):
        self.production = load_production()[0]

    def test_concrete_takes_lime_pozzolana_and_aggregate(self):
        concrete = self.production["concrete_pozzolanic_kg"]
        for material in ("lime_kg", "pozzolana_kg", "stone_kg"):
            self.assertGreater(concrete["inputs"].get(material, 0.0), 0.0, material)
        self.assertEqual(concrete["requires_node"], "mat_pozzolana")

    def test_concrete_balances_mass(self):
        concrete = self.production["concrete_pozzolanic_kg"]
        total_in = sum(concrete["inputs"].values())
        self.assertAlmostEqual(total_in, concrete["outputs"]["concrete_pozzolanic_kg"], delta=0.03 * total_in)

    def test_mortar_runs_between_one_and_three_parts_pozzolana_to_one_of_lime_putty(self):
        inputs = self.production["concrete_pozzolanic_kg"]["inputs"]
        solids_per_kg_quicklime = CALCIUM_HYDROXIDE_MOLAR_MASS / CALCIUM_OXIDE_MOLAR_MASS
        putty_kg = inputs["lime_kg"] * solids_per_kg_quicklime * 2.0   # putty is about half solids by mass
        self.assertGreater(inputs["pozzolana_kg"] / putty_kg, 1.0)
        self.assertLess(inputs["pozzolana_kg"] / putty_kg, 3.0)

    def test_pozzolana_is_extracted_not_made(self):
        entry = self.production["pozzolana_kg"]
        self.assertEqual(entry["inputs"], {})
        self.assertTrue(entry["extracted_from"])

    def test_pozzolana_occurs_only_in_sourced_volcanic_districts(self):
        places = geography_api.load_geography()["located_materials"]["pozzolana"]["places"]
        self.assertGreaterEqual(len(places), 3)
        for place in places:
            self.assertTrue(place.get("source"), place.get("name"))
            nearest = min(distance_km((place["lat"], place["lon"]), centre)
                          for centre in VOLCANIC_DISTRICT_CENTRES.values())
            self.assertLess(nearest, DISTRICT_RADIUS_KM, place["name"])


CONCRETE_WORKS = ("sea_harbours_pozzolana", "med_aqueducts_latrines", "tr_canal_lock")


class HydraulicConcreteWorksTests(unittest.TestCase):
    """The works that need a binder setting under water or carrying water name Roman concrete."""

    @classmethod
    def setUpClass(cls):
        from sim.content import tree_merge
        cls.nodes = {node["id"]: node for node in tree_merge.build_tree().tree["nodes"]}
        cls.production = load_production()[0]

    def test_each_work_draws_pozzolanic_concrete_by_mass(self):
        for node_id in CONCRETE_WORKS:
            materials = self.nodes[node_id]["mat"]
            self.assertGreater(materials.get("concrete_pozzolanic_kg", 0.0), 0.0, node_id)
            self.assertIn("concrete_pozzolanic_kg", self.production)

    def test_each_work_states_the_source_of_its_mass(self):
        for node_id in CONCRETE_WORKS:
            node = self.nodes[node_id]
            self.assertIn("[BASIS:", node.get("_internal", ""), node_id)
            self.assertIn(node.get("conf"), ("B", "C", "D"), node_id)

    def test_concrete_replaces_the_separate_lime_and_stone_it_contains(self):
        materials = self.nodes["med_aqueducts_latrines"]["mat"]
        self.assertNotIn("lime_kg", materials)
        self.assertNotIn("stone_kg", materials)

    def test_the_pozzolana_distance_multiplier_is_retired(self):
        entry = geography_api.load_geography()["located_materials"]["pozzolana"]
        self.assertEqual(entry["cost_multiplier"], 1)
        self.assertNotIn("HEURISTIC", entry.get("note", ""))


if __name__ == "__main__":
    unittest.main()
