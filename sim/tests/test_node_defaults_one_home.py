"""The base merge and the mod overlay fill the same defaults for a bare node."""
import unittest

from sim.engine import mods, tree_merge
from sim.engine.node_defaults import OPTIONAL_DEFAULTS, STRUCTURAL_DEFAULTS


def _bare():
    return {"id": "bare", "name": "Bare", "cat": "x", "pre": [], "note": ""}


class NodeDefaultsOneHomeTests(unittest.TestCase):
    def test_both_paths_fill_every_default(self):
        from_mods = mods._node_defaults(_bare())
        from_merge = tree_merge.normalise_v2(_bare())
        for field, value in {**OPTIONAL_DEFAULTS, **STRUCTURAL_DEFAULTS}.items():
            self.assertIn(field, from_mods)
            self.assertIn(field, from_merge)
            self.assertEqual(from_mods[field], value, field)
            self.assertEqual(from_merge[field], value, field)
        self.assertEqual(from_mods["yrs"], from_merge["yrs"])
