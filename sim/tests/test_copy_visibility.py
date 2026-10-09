"""Complaint 376: how much of a technique an onlooker can copy is declared on the node.

`copy_visibility` (above 0, at most 1, with `copy_visibility_reason`) is the share of the know-how that shows
in the product or the working yard. A node that declares nothing keeps the count of trades and materials."""

QUICK_TOPIC = True

import types
import unittest

from sim.engine import copy_visibility_defaults, data, society_disclosure, validate_copy_visibility

NODE_WITH_NOTHING_DECLARED = {"lab": {"smith": 5.0, "carpenter": 5.0}, "mat": {"iron_bar_kg": 1.0, "timber_m3": 1.0}}


def difficulty_of(nodes, node_id):
    world = types.SimpleNamespace(nodes=nodes)
    return society_disclosure.DisclosureMixin.copy_difficulty(world, node_id)


class CopyVisibility(unittest.TestCase):

    def test_a_node_declaring_nothing_keeps_the_count_of_trades_and_materials(self):
        self.assertEqual(difficulty_of({"a": NODE_WITH_NOTHING_DECLARED}, "a"), 4)

    def test_a_declared_visibility_replaces_the_count(self):
        node = dict(NODE_WITH_NOTHING_DECLARED, copy_visibility=0.5)
        self.assertEqual(difficulty_of({"a": node}, "a"), 2.0)

    def test_a_fully_visible_technique_is_as_easy_as_the_floor(self):
        node = dict(NODE_WITH_NOTHING_DECLARED, copy_visibility=1.0)
        self.assertEqual(difficulty_of({"a": node}, "a"), 1.0)

    def test_a_hidden_process_is_harder_than_a_visible_device_with_more_parts(self):
        hidden = {"lab": {"artisan": 1.0}, "mat": {}, "copy_visibility": 0.1}
        visible = dict(NODE_WITH_NOTHING_DECLARED, copy_visibility=0.9)
        self.assertGreater(difficulty_of({"h": hidden}, "h"), difficulty_of({"v": visible}, "v"))

    def test_the_validator_wants_a_share_and_a_reason_together(self):
        reason = "the proportions and the corning cannot be seen in the finished powder"
        good = {"a": {"copy_visibility": 0.2, "copy_visibility_reason": reason}}
        self.assertEqual(validate_copy_visibility.check_copy_visibility(good), [])
        for bad in ({"copy_visibility": 0.2}, {"copy_visibility_reason": reason},
                    {"copy_visibility": 0.0, "copy_visibility_reason": reason},
                    {"copy_visibility": 1.5, "copy_visibility_reason": reason},
                    {"copy_visibility": 0.2, "copy_visibility_reason": "hidden"}):
            self.assertEqual(len(validate_copy_visibility.check_copy_visibility({"a": bad})), 1, bad)

    def test_the_real_data_is_valid_and_declares_a_first_set(self):
        _tree, _document, nodes, _wages, _goods = data.load()
        self.assertEqual(validate_copy_visibility.check_copy_visibility(nodes), [])
        declared = {node_id: node["copy_visibility"] for node_id, node in nodes.items() if "copy_visibility" in node}
        self.assertGreaterEqual(len(declared), 8)
        self.assertLess(declared["gunpowder"], declared["lnd_wheelbarrow"])
        self.assertLess(declared["crucible_steel"], declared["tl_stirrup"])

    def test_a_node_declaring_nothing_takes_its_categorys_entry(self):
        categories = {"loom": {"copy_visibility": 0.8, "reason": "The frame is open to view and can be copied."}}
        nodes = [{"id": "a", "cat": "loom"}, {"id": "b", "cat": "loom", "copy_visibility": 0.1, "copy_visibility_reason": "own"},
                 {"id": "c", "cat": "unknown"}]
        self.assertEqual(copy_visibility_defaults.apply_defaults(nodes, categories), 1)
        self.assertEqual(nodes[0]["copy_visibility"], 0.8)
        self.assertEqual(nodes[0]["copy_visibility_basis"], "category")
        self.assertEqual(nodes[1]["copy_visibility"], 0.1)
        self.assertNotIn("copy_visibility", nodes[2])
        self.assertEqual(difficulty_of({"a": nodes[0]}, "a"), 1.25)

    def test_the_category_table_is_checked(self):
        self.assertEqual(validate_copy_visibility.check_category_table(copy_visibility_defaults.table()), [])
        bad = {"x": {"copy_visibility": 0.0, "reason": "The frame is open to view and can be copied."}, "y": {"copy_visibility": 0.5, "reason": "short"}}
        self.assertEqual(len(validate_copy_visibility.check_category_table(bad)), 2)

    def test_every_shipped_node_declares_how_much_of_it_shows(self):
        _tree, _document, nodes, _wages, _goods = data.load()
        self.assertEqual(copy_visibility_defaults.undeclared(nodes), [])
        self.assertEqual(validate_copy_visibility.check_copy_visibility(nodes), [])
        self.assertEqual(nodes["gunpowder"]["copy_visibility"], 0.15)       # a node's own declaration stands
        self.assertNotIn("copy_visibility_basis", nodes["gunpowder"])
        taken = [node for node in nodes.values() if node.get("copy_visibility_basis") == "category"]
        self.assertGreater(len(taken), len(nodes) // 2)

    def test_what_shows_follows_the_kind_of_thing(self):
        table = copy_visibility_defaults.table()
        self.assertGreater(table["bridges"]["copy_visibility"], table["organic_chemistry"]["copy_visibility"])
        self.assertGreater(table["wind_prime"]["copy_visibility"], table["alloys"]["copy_visibility"])


if __name__ == "__main__":
    unittest.main()
