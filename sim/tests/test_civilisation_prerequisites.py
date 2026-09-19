"""A civilisation's starting_techs must not break the tree's own prerequisite
graph. Seventeen currently do, and this file pins exactly which.

Complaints/42. `data/civilizations/*.json` lists `starting_techs` as a flat
set of node ids, and `data/tech_tree.json` gives every node a `pre` list.
Nothing had ever compared the two, so a civilisation can hold a node while
lacking the thing that node is built on - england_1300 holds
`water_power_scale` without `crank_conrod`, rome_100ad holds `civ_dome_roman`
without `mat_pozzolana` although its own prose says Rome has pozzolana.

PINNED, NOT FIXED, AND DELIBERATELY SO. Each violation is individually
arguable: some want the prerequisite added to the civilisation, some want the
tree's `pre` corrected, and mexica_1500's three want a rethink of which way
the dependency runs, since gating maize and chinampa agriculture on European
contact is coherent for a European civilisation and incoherent for this one.
Deciding seventeen historical questions is not this file's job. Stopping the
number growing is.

So this test fails in BOTH directions, on purpose:
  - a new violation fails, which is the point;
  - fixing one also fails, with a message saying to lower the pin, so the fix
    is recorded rather than letting the count drift quietly.

Same pattern test_price_solver_cycles.py used while Complaints/31 was open. A
green suite pinning a known defect gets acted on; a red one gets ignored.

SCOPE. First level only: a held node's immediate `pre`. It does not check
closure over the full transitive chain, and it says nothing about whether a
civilisation SHOULD hold something it does not - that is Complaints/41's
question and needs a historian, not a graph walk.
"""
import json
import glob
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(ROOT, "data")
if not os.path.isdir(DATA):                      # running from sim/tests/
    DATA = os.path.join(os.path.dirname(os.path.dirname(HERE)), "data")


# Every violation as it stands today, keyed (civilisation, held node) with the
# prerequisites that node needs and the civilisation does not have. Generated
# by measurement, not by hand.
KNOWN_VIOLATIONS = {
    ("england_1300", "mat_paper"): ["rag_paper"],
    ("england_1300", "sea_sternpost_rudder"): ["sea_skeleton_first"],
    ("england_1300", "tex_indigo"): ["mat_natron"],
    ("england_1300", "water_power_scale"): ["crank_conrod"],
    ("han_china_100ad", "bellows_water_blown"): ["refractory_fireclay", "water_power_scale"],
    ("han_china_100ad", "blast_furnace"): ["charcoal_industrial"],
    ("han_china_100ad", "cap_heat_1300"): ["cap_heat_1100"],
    ("han_china_100ad", "fud_heavy_mouldboard_plough_coulter"): ["horse_collar"],
    ("han_china_100ad", "fud_seed_drill"): ["horse_collar", "master_screw"],
    ("han_china_100ad", "mat_paper"): ["rag_paper"],
    ("mexica_1500", "fud_cacao"): ["exp_americas_factory"],
    ("mexica_1500", "fud_chinampa"): ["exp_americas_factory"],
    ("mexica_1500", "fud_maize"): ["exp_americas_factory"],
    ("norse_900ad", "exp_openocean_navigation"): [
        "clock_pendulum", "opt_sextant", "sea_magnetic_compass", "world_map"],
    ("norse_900ad", "med_trepanation"): ["med_surgical_kit_good"],
    ("norse_900ad", "med_wound_suturing"): ["med_surgical_kit_good"],
    ("rome_100ad", "civ_dome_roman"): ["mat_pozzolana"],
}


def load_tree_nodes():
    with open(os.path.join(DATA, "tech_tree.json")) as handle:
        nodes = json.load(handle)["nodes"]
    if isinstance(nodes, list):
        nodes = {node["id"]: node for node in nodes}
    return nodes


def load_civilisations():
    civilisations = {}
    for path in sorted(glob.glob(os.path.join(DATA, "civilizations", "*.json"))):
        name = os.path.basename(path)[:-len(".json")]
        if name.startswith("_"):
            continue
        with open(path) as handle:
            civilisations[name] = set(json.load(handle).get("starting_techs") or [])
    return civilisations


def measure_violations():
    """{(civilisation, node_id): [missing prerequisites]} over every civ."""
    nodes = load_tree_nodes()
    found = {}
    for name, held in load_civilisations().items():
        for node_id in held:
            node = nodes.get(node_id)
            if node is None:
                continue
            missing = sorted(prereq_id for prereq_id in (node.get("pre") or []) if prereq_id not in held)
            if missing:
                found[(name, node_id)] = missing
    return found


class CivilisationPrerequisiteTests(unittest.TestCase):

    def test_no_civilisation_gained_a_new_prerequisite_violation(self):
        found = measure_violations()
        added = sorted(set(found) - set(KNOWN_VIOLATIONS))
        self.assertEqual(added, [], (
            "New starting_techs prerequisite violation(s): %s. A civilisation "
            "now holds a node whose own `pre` it does not have. Either give it "
            "the prerequisite, or correct the node's `pre` - see Complaints/42."
            % ", ".join("%s/%s" % pair for pair in added)))

    def test_a_fixed_violation_lowers_the_pin(self):
        found = measure_violations()
        fixed = sorted(set(KNOWN_VIOLATIONS) - set(found))
        self.assertEqual(fixed, [], (
            "Violation(s) fixed and not yet un-pinned: %s. Good - remove them "
            "from KNOWN_VIOLATIONS in this file so the count can only go down. "
            "This failure is the fix being recorded, not a regression."
            % ", ".join("%s/%s" % pair for pair in fixed)))

    def test_the_missing_prerequisites_are_still_the_same_ones(self):
        # Catches a violation that stayed but changed shape - a node gaining a
        # second unmet prerequisite would otherwise pass both tests above.
        found = measure_violations()
        changed = sorted(key for key in set(found) & set(KNOWN_VIOLATIONS)
                         if found[key] != KNOWN_VIOLATIONS[key])
        self.assertEqual(changed, [], (
            "Known violation(s) changed shape: %s. The node is still held "
            "without its prerequisites, but WHICH prerequisites are missing "
            "has moved."
            % ", ".join("%s/%s" % pair for pair in changed)))

    def test_every_pinned_violation_names_a_real_node(self):
        # A pin naming a node that no longer exists would silently never fire.
        nodes = load_tree_nodes()
        civilisations = load_civilisations()
        for civilisation, node_id in KNOWN_VIOLATIONS:
            self.assertIn(civilisation, civilisations)
            self.assertIn(node_id, nodes, "%s pins a node not in the tree" % node_id)


if __name__ == "__main__":
    unittest.main()
