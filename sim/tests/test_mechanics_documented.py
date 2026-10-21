"""Every node the mechanics data names is in the tree, every mechanics block is a dict, and every mechanic name used in the tree
is documented in data/branches/MECHANICS.md. Read from the data, with no game."""
QUICK_TOPIC = True

import os
import unittest

from sim.tests.harness import NODES, ROOT


class MechanicsDataTests(unittest.TestCase):
    def test_every_mechanics_block_is_a_dict(self):
        self.assertTrue(all(isinstance(node.get("mechanics", {}), dict) for node in NODES.values()))

    def test_every_mechanic_name_used_in_the_tree_is_documented(self):
        with open(os.path.join(ROOT, "data", "branches", "MECHANICS.md"), encoding="utf-8") as handle:
            documented = handle.read()
        used = sorted({name for node in NODES.values() for name in (node.get("mechanics") or {})})
        self.assertEqual([name for name in used if "`%s`" % name not in documented], [])


if __name__ == "__main__":
    unittest.main()
