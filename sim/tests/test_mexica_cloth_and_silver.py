"""Complaints/463: the Mexica start holds a technique for cloth, fabric and silver."""
import json
import os
import unittest

from sim.engine.catalog import load_production_catalog

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MexicaClothAndSilver(unittest.TestCase):

    def test_each_good_has_an_entry_gated_on_a_node_the_mexica_hold(self):
        with open(os.path.join(ROOT, "data", "civilizations", "mexica_1500.json")) as handle:
            civilisation = json.load(handle)
        held = set(civilisation["starting_techs"])
        production = load_production_catalog(ROOT)
        for good in ("cloth_kg", "fabric_kg", "silver_kg"):
            gates = [entry.get("requires_node") for entry in production.values()
                     if good in entry.get("outputs", {})]
            self.assertTrue(any(gate is None or gate in held for gate in gates), good)
            self.assertNotIn(good, civilisation["unsupplied_basket_goods"])


if __name__ == "__main__":
    unittest.main()
