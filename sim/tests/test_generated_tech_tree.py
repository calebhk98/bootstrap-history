"""Complaints/141 and 280: the tech tree is built from the branch files at
load time and is never committed; option ids in alternative groups must name
something real.

The branch files are the only source. A tree built from them, cached on the
content of everything the build reads, can never be stale, so no file in the
repository holds a copy.
"""
import json
import os
import re
import subprocess
import tempfile
import unittest
from unittest import mock

from sim import treetool
from sim.engine import cli, tree_source

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GENERATED_NAME = "tech_" + "tree.json"


def _node(node_id, **overrides):
    node = {"id": node_id, "name": node_id, "cat": "test", "pre": [],
            "note": "fixture", "kind": "ENGINEERING"}
    node.update(overrides)
    return node


class FixtureBranches(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.branches = os.path.join(self.directory, "branches")
        self.cache = os.path.join(self.directory, "cache")
        os.makedirs(self.branches)
        patch = mock.patch.object(treetool, "BR", self.branches)
        patch.start()
        self.addCleanup(patch.stop)
        self.write_meta({"goal_node": "fx_alpha", "goals": []})
        self.write_branch("10_fixture.json", [_node("fx_alpha"),
                                              _node("fx_beta", pre=["fx_alpha"])])

    def write_branch(self, filename, nodes):
        with open(os.path.join(self.branches, filename), "w") as handle:
            json.dump(nodes, handle)

    def write_meta(self, meta):
        with open(os.path.join(self.branches, tree_source.META_FILE), "w") as handle:
            json.dump(meta, handle)

    def load(self):
        return tree_source.load_base_tree(cache_directory=self.cache)


class LoaderBuildsFromBranches(FixtureBranches):
    def test_nodes_and_meta_come_from_the_branch_directory(self):
        tree = self.load()
        self.assertEqual({node["id"] for node in tree["nodes"]}, {"fx_alpha", "fx_beta"})
        self.assertEqual(tree["meta"]["goal_node"], "fx_alpha")
        self.assertEqual(tree["nodes"][0]["kind"], "ENGINEERING")

    def test_an_edit_to_a_branch_file_is_seen_by_the_next_load(self):
        self.load()
        self.write_branch("10_fixture.json", [_node("fx_alpha", cap=424242),
                                              _node("fx_beta", pre=["fx_alpha"])])
        nodes = {node["id"]: node for node in self.load()["nodes"]}
        self.assertEqual(nodes["fx_alpha"]["cap"], 424242)

    def test_a_warm_cache_skips_the_build_and_returns_the_same_tree(self):
        cold = self.load()
        with mock.patch.object(treetool, "build_tree",
                               side_effect=AssertionError("rebuilt on a warm cache")):
            warm = self.load()
        self.assertEqual(cold, warm)

    def test_each_call_returns_a_tree_the_caller_may_mutate(self):
        self.load()["nodes"].clear()
        self.assertEqual(len(self.load()["nodes"]), 2)

    def test_a_changed_branch_file_changes_the_cache_key(self):
        before = tree_source.input_digest()
        self.write_branch("20_more.json", [_node("fx_gamma")])
        self.assertNotEqual(before, tree_source.input_digest())

    def test_an_unreadable_cache_directory_still_loads(self):
        with open(self.cache, "w") as handle:
            handle.write("not a directory")
        self.assertEqual(len(self.load()["nodes"]), 2)


class RepositoryDoesNotCommitTheTree(unittest.TestCase):
    def test_the_generated_file_is_ignored(self):
        with open(os.path.join(ROOT, ".gitignore")) as handle:
            lines = [line.strip() for line in handle]
        self.assertIn("data/" + GENERATED_NAME, lines)

    def test_the_generated_file_is_not_tracked(self):
        try:
            listed = subprocess.run(["git", "ls-files", "data/" + GENERATED_NAME],
                                    cwd=ROOT, capture_output=True, text=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("not a git checkout")
        self.assertEqual(listed.stdout.strip(), "")

    def test_only_the_tree_tool_names_the_generated_file_in_code(self):
        offenders = []
        for directory, subdirectories, filenames in os.walk(os.path.join(ROOT, "sim")):
            subdirectories[:] = [name for name in subdirectories if name != "__pycache__"]
            for filename in filenames:
                path = os.path.join(directory, filename)
                if not filename.endswith(".py") or filename == "treetool.py" \
                        or path == os.path.abspath(__file__):
                    continue
                with open(path, encoding="utf-8") as handle:
                    for number, line in enumerate(handle, 1):
                        code = line.split("#", 1)[0]
                        if re.search(r"""["']%s["']""" % re.escape(GENERATED_NAME), code):
                            offenders.append("%s:%d" % (os.path.relpath(path, ROOT), number))
        self.assertEqual(offenders, [], "read the tree through sim.engine.tree_source")


class RealBranchesBuildTheWholeTree(unittest.TestCase):
    def test_the_built_tree_carries_every_field_the_engine_reads(self):
        tree = tree_source.load_base_tree()
        nodes = {node["id"]: node for node in tree["nodes"]}
        self.assertGreater(len(nodes), 1000)
        self.assertIn(tree["meta"]["goal_node"], nodes)
        self.assertTrue(tree["meta"]["goals"])
        self.assertTrue(any(node.get("kind") == "SCIENCE" for node in nodes.values()))
        self.assertTrue(any(node.get("_internal") for node in nodes.values()))
        self.assertIn("lnd_whippletree", nodes)

    def test_building_the_real_branches_loses_nothing(self):
        result = treetool.build_tree()
        self.assertEqual(result.losses, [])
        self.assertEqual(result.collisions, [])


class OptionIdsNameRealThings(unittest.TestCase):
    NODES = {"el2_dynamo": {"id": "el2_dynamo"}, "el2_plater": {"id": "el2_plater"}}

    def check(self, options, goods=("copper_kg",)):
        node = {"id": "el2_plater", "pre": [],
                "req_any": [{"group": "current", "options": options}]}
        return cli._check_node_option_ids("el2_plater", node, self.NODES, set(goods))

    def test_a_node_id_is_accepted(self):
        self.assertEqual(self.check({"el2_dynamo": 1.0}), [])

    def test_a_good_is_accepted(self):
        self.assertEqual(self.check({"copper_kg": 1.0}), [])

    def test_a_free_commodity_is_accepted(self):
        self.assertEqual(self.check({"oil_bath": 1.0}), [])

    def test_a_node_id_missing_its_own_prefix_is_an_error(self):
        errors = self.check({"dynamo": 1.0})
        self.assertEqual(len(errors), 1)
        self.assertIn("el2_dynamo", errors[0])
        self.assertIn("current", errors[0])

    def test_electroplating_options_name_real_nodes(self):
        tree = tree_source.load_base_tree()
        nodes = {node["id"]: node for node in tree["nodes"]}
        groups = {group["group"]: group for group in
                  nodes["el2_electroplating_and_electrorefining"]["req_any"]}
        for option in groups["current_source"]["options"]:
            self.assertIn(option, nodes)

    def test_no_node_in_the_real_tree_has_a_misspelt_option(self):
        tree = tree_source.load_base_tree()
        nodes = {node["id"]: node for node in tree["nodes"]}
        goods = treetool.load_material_namespace(tree["nodes"])
        errors = [error for node_id, node in nodes.items()
                  for error in cli._check_node_option_ids(node_id, node, nodes, goods)]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()


class LaterFilePrerequisites(unittest.TestCase):
    """The prefix repair must see ids defined in branch files that sort later:
    `cap_power_grid` asks for `power_grid`, defined in a later file, and must not
    be rewired onto itself."""

    @classmethod
    def setUpClass(cls):
        cls.built = {node["id"]: node for node in treetool.build_tree().tree["nodes"]}
        branch_directory = os.path.join(os.path.dirname(HERE), "..", "data", "branches")
        cls.authored = {}
        for filename in sorted(os.listdir(branch_directory)):
            if not filename.endswith(".json"):
                continue
            batch = json.load(open(os.path.join(branch_directory, filename)))
            if isinstance(batch, list):
                for node in batch:
                    if isinstance(node, dict) and "id" in node:
                        cls.authored[node["id"]] = node

    def test_prerequisite_defined_in_a_later_file_survives(self):
        self.assertIn("power_grid", self.built["cap_power_grid"]["pre"])

    def test_no_authored_prerequisite_naming_a_real_node_is_dropped(self):
        dropped = [(node_id, prerequisite) for node_id, node in self.authored.items()
                   if node_id in self.built
                   for prerequisite in node.get("pre", [])
                   if prerequisite in self.authored and prerequisite not in self.built[node_id]["pre"]]
        self.assertEqual(dropped, [])
