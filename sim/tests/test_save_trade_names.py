"""Complaint 640 (an England break test): teaching a trade must not destroy the save. `trades_created` holds trade names, which
the save check reads against the wage table and not against the tech tree; node-id sets are read against the tree. Each check
function is called on a blob written out here."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.data import WAGES
from sim.engine.saveload import _check_save_node_id_references, _check_save_trade_name_sets


def trades(*names, field="trades_created"):
    return {field: {"__set__": list(names)}}


class SaveTradeNames(unittest.TestCase):
    def test_a_trade_the_game_has_but_the_tree_has_no_node_for_is_accepted(self):
        self.assertIn("optician", WAGES)
        self.assertIsNone(_check_save_trade_name_sets(trades("optician")))

    def test_a_trade_the_game_does_not_have_is_refused_by_name(self):
        message = _check_save_trade_name_sets(trades("optician", "alchemist"))
        self.assertIn("alchemist", message)

    def test_endemic_trades_are_read_the_same_way(self):
        self.assertIsNone(_check_save_trade_name_sets(trades("optician", field="trades_endemic")))

    def test_a_trade_name_set_that_is_not_a_set_of_strings_is_corrupt(self):
        self.assertIn("corrupt", _check_save_trade_name_sets({"trades_created": {"__set__": [1, 2]}}))

    def test_trade_names_are_not_read_as_node_ids(self):
        game = types.SimpleNamespace(nodes={"stone_cutting": {}})
        self.assertEqual(_check_save_node_id_references(trades("optician"), game), (None, set()))

    def test_a_node_id_the_tree_lacks_is_reported_unknown(self):
        game = types.SimpleNamespace(nodes={"stone_cutting": {}})
        self.assertEqual(_check_save_node_id_references(trades("stone_cutting", "lost_art", field="done"), game),
                         (None, {"lost_art"}))


if __name__ == "__main__":
    unittest.main()
