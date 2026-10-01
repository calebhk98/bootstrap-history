"""Roman-only content is not offered to a civilisation as local fact (Complaints/231).

Nodes that are Mediterranean artefacts sit behind the civilisation's own
`needs_first` gate in a civilisation with no contact with the Mediterranean;
generic technology carries a neutral name; kit descriptions name no Roman
institution.
"""
import json
import os
import unittest

from sim import civ_start_check as start_check
from sim.engine import data

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

MEDITERRANEAN_ARTEFACTS = (
    "civ_aqueduct_roman", "civ_dome_roman", "civ_insula", "civ_chorobates",
    "civ_surveying_groma", "hom_cosmetics_roman", "mat_papyrus", "med_valetudinaria")
GENERIC_TECHNOLOGY = ("civ_arch_roman", "civ_brick_tile", "civ_road_paved", "civ_sewer_roman")
NO_MEDITERRANEAN_CONTACT = ("han_china_100ad", "mexica_1500")


def _nodes():
    with open(os.path.join(ROOT, "data", "tech_tree.json")) as handle:
        return {node["id"]: node for node in json.load(handle)["nodes"]}


class RomanContentNotLocalFact(unittest.TestCase):
    def test_mediterranean_artefacts_are_gated_where_there_is_no_contact(self):
        civilisations = start_check.load_civilisations(ROOT)
        for name in NO_MEDITERRANEAN_CONTACT:
            civilisation = civilisations[name]
            gated = start_check.gated_ids(civilisation, set(civilisation["starting_techs"]))
            for node_id in MEDITERRANEAN_ARTEFACTS:
                self.assertIn(node_id, gated, "%s can start %s" % (name, node_id))

    def test_generic_technology_is_not_named_for_rome(self):
        nodes = _nodes()
        for node_id in GENERIC_TECHNOLOGY:
            self.assertNotIn("roman", nodes[node_id]["name"].lower(), node_id)

    def test_kit_descriptions_name_no_roman_institution(self):
        for kit_id, kit in data.STARTING_KITS.items():
            text = kit["desc"].lower()
            for word in ("equestrian", "senatorial", "denarii"):
                self.assertNotIn(word, text, kit_id)


if __name__ == "__main__":
    unittest.main()
