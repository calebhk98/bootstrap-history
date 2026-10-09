"""Complaints/309: the disposal sink data agrees with the geography module, and every heap is of a real material."""

QUICK_TOPIC = True

import json
import unittest

from sim.engine import disposal_cost, validate_production
from sim.geography import api as geography
from sim.world import demand

SINK_KEYS = ("waste_handling_job", "waste_haulage_on_foot", "waste_haulage_by_pack_animal",
             "waste_haulage_by_cart", "dump_ground_m2")
HAULAGE_BY_MODE = {"waste_haulage_on_foot": "foot", "waste_haulage_by_pack_animal": "pack",
                   "waste_haulage_by_cart": "cart"}


class SinkAgreesWithGeographyTests(unittest.TestCase):

    def setUp(self):
        self.production = demand.production_data()
        self.rates = geography.carriage_rates(["foot", "pack", "cart"])

    def test_each_haulage_technique_costs_its_modes_crew_hours_per_tonne_kilometre(self):
        for key, mode in HAULAGE_BY_MODE.items():
            stated = self.production[key]["labour_hours"]["labourer"]
            self.assertAlmostEqual(stated / self.rates[mode]["crew_hours_per_tonne_km"], 1.0, places=2, msg=key)

    def test_handling_is_the_modes_load_and_unload_hours_per_tonne(self):
        stated = self.production["waste_handling_job"]["labour_hours"]["labourer"]
        for mode in ("foot", "pack", "cart"):
            self.assertEqual(stated, self.rates[mode]["handling_hours_per_tonne"])

    def test_the_services_are_well_formed_production_entries(self):
        for key in SINK_KEYS:
            entry = self.production[key]
            self.assertEqual(validate_production.check_has_source(key, entry), [], key)
            self.assertEqual(validate_production.check_unit_dimension(key, entry), [], key)
            self.assertEqual(validate_production.check_conf(key, entry), [], key)
            self.assertEqual(validate_production.check_yield_basis(key, entry), [], key)

    def test_a_service_with_nothing_to_consume_is_still_rejected(self):
        self.assertTrue(validate_production.check_has_source("x", {"outputs": {"x": 1.0}}))
        self.assertTrue(validate_production.check_has_source(
            "x", {"outputs": {"x": 1.0}, "service": True}))

    def test_the_services_are_the_ones_the_disposal_module_reads(self):
        made = {material for key in SINK_KEYS for material in self.production[key]["outputs"]}
        self.assertEqual(made, {disposal_cost.HANDLING_SERVICE, disposal_cost.HAULAGE_SERVICE,
                                disposal_cost.GROUND_SERVICE})


class WasteHeapDataTests(unittest.TestCase):

    def setUp(self):
        with open(disposal_cost.WASTE_HEAPS_FILE) as handle:
            self.materials = json.load(handle)["materials"]
        made = {material for entry in demand.production_data().values() for material in entry["outputs"]}
        self.made = made

    def test_every_heap_is_of_a_material_something_makes(self):
        self.assertFalse(set(self.materials) - self.made)

    def test_every_heap_states_positive_figures_with_a_source_and_confidence(self):
        for material, record in self.materials.items():
            self.assertGreater(record["bulk_density_kg_per_m3"], 0.0, material)
            self.assertGreater(record["heap_height_m"], 0.0, material)
            self.assertIn(record["conf"], ("A", "B", "C", "D"), material)
            self.assertTrue(record["source"], material)

    def test_every_joint_by_product_that_can_be_a_waste_has_a_heap_of_its_own(self):
        wastes = {"basic_slag_kg", "coal_tar_kg", "wood_tar_kg"}
        self.assertFalse(wastes - set(self.materials))


if __name__ == "__main__":
    unittest.main()
