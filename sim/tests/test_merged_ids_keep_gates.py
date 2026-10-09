"""Complaint 133: a merged-away id resolves to its survivor, and the gates of the duplicate pairs are not lost.

Reads the authored branch files and the merge in memory; nothing here builds a game."""

QUICK_TOPIC = True

import glob
import json
import os
import unittest

from sim.engine import tree_merge

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_GATE_FIELDS = ("requires_running", "requires_ways")
# The audit's duplicate pairs that are two live nodes (not in the retired list): each twin's operating
# dependents must need a work running.
_LIVE_TWINS = (("civ_aqueduct_roman", "cn_aqueduct"), ("civ_sewer_roman", "cn_sewer_system"))


def _authored():
    found = {}
    for path in sorted(glob.glob(os.path.join(_ROOT, "data", "branches", "[0-9]*.json"))):
        with open(path) as handle:
            data = json.load(handle)
        for node in (data["nodes"] if isinstance(data, dict) else data):
            found.setdefault(node["id"], []).append(node)
    return found


class MergedIdsKeepGates(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        built = tree_merge.build_tree()
        cls.nodes = {node["id"]: node for node in built.tree["nodes"]}
        cls.retired = built.tree["meta"]["merged_duplicate_ids"]
        cls.authored = _authored()

    def test_every_merged_away_id_resolves_to_a_live_survivor(self):
        for retired_id, survivor in sorted(self.retired.items()):
            self.assertNotIn(retired_id, self.nodes, retired_id)
            self.assertIn(survivor, self.nodes, "%s merged into a node that does not exist" % retired_id)
            self.assertNotIn(survivor, self.retired, "%s merged into a retired id" % retired_id)

    def test_no_gate_names_a_merged_away_id(self):
        for node_id, node in sorted(self.nodes.items()):
            for work in node.get("requires_running") or ():
                self.assertNotIn(work, self.retired, "%s requires_running names retired %s" % (node_id, work))

    def test_the_survivor_keeps_every_gate_a_merged_away_id_carried(self):
        for retired_id, survivor in sorted(self.retired.items()):
            for node in self.authored.get(retired_id, ()):
                for field in _GATE_FIELDS:
                    carried = node.get(field)
                    if not carried:
                        continue
                    kept = self.nodes[survivor].get(field) or ()
                    wanted = ([self.retired.get(work, work) for work in carried] if isinstance(carried, list)
                              else carried)
                    for item in wanted:
                        self.assertIn(item, kept, "%s -> %s lost %s %s" % (retired_id, survivor, field, item))

    def test_merge_rewrites_a_retired_id_in_requires_running(self):
        nodes = {"lamp": {"id": "lamp", "pre": [], "requires_running": ["old_grid", "kept_work"]},
                 "grid": {"id": "grid", "pre": []}, "kept_work": {"id": "kept_work", "pre": []}}
        tree_merge._merge_resolve_prerequisites(nodes, {"old_grid": "grid"}, [])
        self.assertEqual(nodes["lamp"]["requires_running"], ["grid", "kept_work"])

    def test_each_live_twin_gates_its_own_operating_dependents(self):
        for pair in _LIVE_TWINS:
            for twin in pair:
                self.assertIn(twin, self.nodes)
                for node_id, node in sorted(self.nodes.items()):
                    operates = (node.get("up") or node.get("up_hours") or node.get("rev_hours") or 0) > 0
                    if twin in node["pre"] and operates and node_id not in pair:
                        self.assertTrue(node.get("requires_running"),
                                        "%s depends on %s but needs no work running" % (node_id, twin))


if __name__ == "__main__":
    unittest.main()
