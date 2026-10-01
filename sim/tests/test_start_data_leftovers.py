"""Starts agree with themselves: needle and fireclay (Complaints/297)."""
import json
import os
import unittest

from sim.engine.tree_source import load_base_tree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FOUNDER_SETUP_NODES = ("workshop_first", "identity_cover", "patron_local")


def _nodes():
    return {node["id"]: node for node in load_base_tree()["nodes"]}


def _closure(nodes, node_id, seen=None):
    seen = set() if seen is None else seen
    for prerequisite in nodes[node_id].get("pre") or []:
        if prerequisite not in seen:
            seen.add(prerequisite)
            _closure(nodes, prerequisite, seen)
    return seen


class NeedleAndFireclay(unittest.TestCase):
    def test_a_hand_needle_node_sits_on_the_millimetre_rung(self):
        nodes = _nodes()
        hand = [node for node in nodes.values()
                if "needle" in node["id"] and node.get("pre") == ["cap_tol_1mm"]]
        self.assertTrue(hand, "no hand-needle node on cap_tol_1mm")

    def test_machine_and_steel_needles_keep_the_tenth_millimetre_rung(self):
        nodes = _nodes()
        for node_id in ("tx2_needle", "tx2_eye_pointed_needle"):
            self.assertIn("cap_tol_100um", nodes[node_id]["pre"])

    def test_fireclay_does_not_need_the_founders_setup_nodes(self):
        # Clay, sand and a kiln: nothing in the physics needs the founder's laboratory.
        nodes = _nodes()
        closure = _closure(nodes, "refractory_fireclay")
        for setup_node in FOUNDER_SETUP_NODES:
            self.assertNotIn(setup_node, closure)

    def test_societies_holding_the_1100_rung_can_hold_fireclay(self):
        nodes = _nodes()
        for name in ("rome_100ad", "england_1300", "norse_900ad", "han_china_100ad"):
            with open(os.path.join(ROOT, "data", "civilizations", name + ".json")) as handle:
                held = set(json.load(handle)["starting_techs"])
            self.assertIn("refractory_fireclay", held)
            self.assertFalse(set(nodes["refractory_fireclay"]["pre"]) - held, name)


class ZincNodes(unittest.TestCase):
    def test_industrial_zinc_scales_up_the_retort_technique(self):
        # Complaints/40: two zinc nodes were alternatives with unrelated prerequisites.
        # The industry node builds on the technique and needs no steelmaking.
        nodes = _nodes()
        self.assertIn("mt2_zinc_by_retort", nodes["zinc_metal"]["pre"])
        self.assertNotIn("cementation_steel", _closure(nodes, "zinc_metal"))

    def test_citric_and_chromate_recipes_name_their_own_process_nodes(self):
        # Complaints/40: the recipes pointed at nodes for other processes.
        nodes = _nodes()
        with open(os.path.join(ROOT, "data", "production", "50_chemicals.json")) as handle:
            recipes = json.load(handle)["materials"]
        for material, node_id in (("citric_acid_kg", "ch2_citric_lime_precipitate"),
                                  ("chrome_salts_kg", "ch2_chromate_from_chromite")):
            self.assertIn(node_id, nodes)
            self.assertEqual(recipes[material]["requires_node"], node_id)


class NotesNotAddressedToRome(unittest.TestCase):
    def test_notes_do_not_address_one_civilisation_by_name(self):
        # Complaints/227: generic nodes spoke to a Roman player in the second person.
        phrases = ("from Britain to India", "to the Rhine", "Rome to the Rhine",
                   "will not reach the Mediterranean", "a rationibus", "software automation",
                   "libraries of the Empire")
        for node in _nodes().values():
            note = node.get("note") or ""
            for phrase in phrases:
                self.assertNotIn(phrase, note, node["id"])


class FortificationUpkeep(unittest.TestCase):
    def test_large_masonry_fortifications_cost_upkeep_and_label_the_rate(self):
        # Complaints/245: a built bastion was never maintained; lime mortar and stone need repair.
        nodes = _nodes()
        for node_id in ("mil_trace_italienne", "mil_bastion"):
            node = nodes[node_id]
            self.assertGreater(node["up_hours"], 0, node_id)
            self.assertIn("HEURISTIC", node.get("_internal", ""), node_id)


if __name__ == "__main__":
    unittest.main()
