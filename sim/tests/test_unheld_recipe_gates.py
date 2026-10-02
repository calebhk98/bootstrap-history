"""Complaints/40: technologies a recipe needs that no civilisation starts with.

The sweep looks only at the frontier: recipe gates held by nobody whose own
prerequisites somebody does hold. Every one is either reviewed here with a
reason, or held. A new unreviewed gap fails; holding a reviewed one fails too,
so the list only ever records the current judgement.
"""
import os
import unittest

from sim import civ_start_check as start_check
from sim.engine.catalog import load_production_catalog
from sim.engine.tree_source import load_base_tree

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Gate node -> why no civilisation holds it.
LEFT_UNHELD = {
    "ag2_hopping": "hopped beer reaches England after 1300; Norse hop growing is not attested",
    "ag2_pyrethrum": "no sourced start civilisation used pyrethrum as an insecticide",
    "chm_phosphorus_extraction": "phosphorus is isolated in the 1600s",
    "finery_puddling": "the finery is a late medieval step and puddling is 1784",
    "fud_pepper_cultivation": "Rome and Han buy pepper; growing it is a trade question, not a start technology",
    "mat_antimony": "metallic antimony was rare in antiquity (Roman stibium is the sulfide); needs a historian",
    "mat_cryolite": "Greenland cryolite is mined from the 1850s",
    "mat_porcelain": "Han high-fired stoneware is not yet porcelain; needs a historian",
    "tx2_cashmere": "Kashmir goat fibre is outside the modelled start regions",
    "tx2_jute_fibre": "Bengal jute is outside the modelled start regions",
    "tx2_mohair": "Anatolian angora goat fibre is outside the modelled start regions",
}


def _frontier():
    nodes = {node["id"]: node for node in load_base_tree()["nodes"]}
    civilisations = start_check.load_civilisations(ROOT)
    production = load_production_catalog(ROOT)
    held = set()
    for civilisation in civilisations.values():
        held |= set(civilisation["starting_techs"])
    gates = {entry["requires_node"] for entry in production.values() if entry.get("requires_node")}
    return {gate for gate in gates - held
            if all(prerequisite in held for prerequisite in nodes[gate].get("pre") or ())}


class UnheldRecipeGateTests(unittest.TestCase):

    def test_every_frontier_gap_is_reviewed(self):
        self.assertEqual(sorted(_frontier() - set(LEFT_UNHELD)), [])

    def test_a_reviewed_gap_that_is_now_held_leaves_the_list(self):
        self.assertEqual(sorted(set(LEFT_UNHELD) - _frontier()), [])

    def test_peat_is_held_where_it_was_the_fuel(self):
        civilisations = start_check.load_civilisations(ROOT)
        # Orkneyinga saga (Torf-Einarr, c. 900) and the turbaries of Domesday Book
        for name in ("norse_900ad", "england_1300"):
            self.assertIn("pwr_peat", civilisations[name]["starting_techs"])


if __name__ == "__main__":
    unittest.main()
