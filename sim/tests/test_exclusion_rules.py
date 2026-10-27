"""The exclusion list (Complaint 230): an entry is a node id, a category or a trait; `exclusion_reason` says which entry excludes a node,
and `exclude` and `include` change the saved list and refuse names that exist nowhere. The rules are called on plain values; the
commands on a stand-in game."""
QUICK_TOPIC = True

import types
import unittest

from sim.projects import exclusion_rules
from sim.projects.api import Exclude, Include
from sim.tests import projects_host
from sim.ui.proto.dispatch_exclusions import _cmd_exclude, _cmd_include

NODES = {"plough": {"cat": "agriculture", "traits": ["tool"], "name": "Plough"},
         "slave_market": {"cat": "labour", "traits": ["buys_people"], "name": "Slave market"},
         "mill": {"cat": "agriculture", "traits": [], "name": "Mill"}}


class _Game:
    def __init__(self, fog=False):
        self.nodes, self.fog = NODES, fog
        self.module = projects_host.build(tree=NODES)

    @property
    def excluded(self):
        return self.module.seat.excluded

    def view(self, name):
        return {"exclusions": self.module.exclusions}[name]

    def send(self, command):
        return {Exclude: self.module.apply_exclude, Include: self.module.apply_include}[type(command)](command)

    def is_visible(self, node_id):
        return node_id != "slave_market"

    def exclusion_entry_known(self, entry):
        return exclusion_rules.entry_known(entry, self.nodes)


class ExclusionReasonTest(unittest.TestCase):
    def test_a_node_is_excluded_by_name_by_category_or_by_trait_and_nothing_else_is(self):
        excluded = {"mill", "category:labour", "trait:tool"}
        self.assertIsNotNone(exclusion_rules.reason(excluded, "mill", NODES))
        self.assertIsNotNone(exclusion_rules.reason(excluded, "slave_market", NODES))
        self.assertIsNotNone(exclusion_rules.reason(excluded, "plough", NODES))
        excluded = {"trait:buys_people"}
        self.assertIsNotNone(exclusion_rules.reason(excluded, "slave_market", NODES))
        self.assertIsNone(exclusion_rules.reason(excluded, "plough", NODES))

    def test_an_empty_list_excludes_nothing(self):
        self.assertIsNone(exclusion_rules.reason(set(), "plough", NODES))

    def test_an_entry_is_known_only_if_it_names_a_node_a_category_or_a_trait_that_exists(self):
        for entry in ("plough", "category:agriculture", "trait:buys_people"):
            self.assertTrue(exclusion_rules.entry_known(entry, NODES), entry)
        for entry in ("no_such_node_anywhere", "category:nothing", "trait:nothing"):
            self.assertFalse(exclusion_rules.entry_known(entry, NODES), entry)


class ExcludeAndIncludeTest(unittest.TestCase):
    def test_exclude_records_the_entry_and_include_removes_it(self):
        game = _Game()
        reply = _cmd_exclude(game, NODES, {"what": "plough"}, None)
        self.assertTrue(reply["ok"])
        self.assertEqual(reply["excluded"], ["plough"])
        self.assertEqual(game.excluded, {"plough"})
        self.assertTrue(_cmd_include(game, NODES, {"what": "plough"}, None)["ok"])
        self.assertEqual(game.excluded, set())

    def test_category_and_trait_entries_are_recorded_and_all_empties_the_list(self):
        game = _Game()
        _cmd_exclude(game, NODES, {"what": "category:agriculture"}, None)
        _cmd_exclude(game, NODES, {"what": "TRAIT:buys_people"}, None)
        self.assertEqual(game.excluded, {"category:agriculture", "trait:buys_people"})
        self.assertTrue(_cmd_include(game, NODES, {"what": "all"}, None)["ok"])
        self.assertEqual(game.excluded, set())

    def test_an_unknown_name_is_refused_and_so_is_including_what_was_never_excluded(self):
        game = _Game()
        self.assertIs(_cmd_exclude(game, NODES, {"what": "no_such_node_anywhere"}, None)["ok"], False)
        self.assertIs(_cmd_include(game, NODES, {"what": "plough"}, None)["ok"], False)
        self.assertEqual(game.excluded, set())

    def test_under_fog_a_node_not_heard_of_cannot_be_excluded(self):
        game = _Game(fog=True)
        self.assertIs(_cmd_exclude(game, NODES, {"what": "slave_market"}, None)["ok"], False)
        self.assertTrue(_cmd_exclude(game, NODES, {"what": "plough"}, None)["ok"])

    def test_bare_exclude_lists_the_entries(self):
        game = _Game()
        game.excluded.add("mill")
        self.assertEqual(_cmd_exclude(game, NODES, {}, None)["excluded"], ["mill"])


if __name__ == "__main__":
    unittest.main()
