"""Complaints/391: England in 1300 can make lye soap; saponification chemistry stays later."""
import os
import unittest

from sim.engine import civ_start_check as start_check
from sim.engine.catalog import load_production_catalog

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SoapKnownToEnglandTests(unittest.TestCase):

    def test_soap_recipe_gate_is_held_at_the_england_start(self):
        civilisations = start_check.load_civilisations(ROOT)
        gate = load_production_catalog(ROOT)["soap_kg"]["requires_node"]
        self.assertIn(gate, civilisations["england_1300"]["starting_techs"])

    def test_saponification_chemistry_is_not_the_soap_gate(self):
        gate = load_production_catalog(ROOT)["soap_kg"]["requires_node"]
        self.assertNotEqual(gate, "ch2_rxn_saponification")


if __name__ == "__main__":
    unittest.main()
