"""engine_content_ids: the engine reads node `mechanics`, never node ids (CLAUDE.md 4.7). No string literal in engine or world
code equals a technology node id. A static scan: a cheap pattern pass over every engine and world module picks the few that
quote a node id, and only those are parsed to find the literal and its line. The engine reading declared mechanics is
`test_engine_content_mechanics`, and the mechanics data checks are `test_mechanics_documented`."""
QUICK_TOPIC = True

import ast
import glob
import os
import re
import unittest

from sim.tests.harness import NODES, ROOT
from sim.tests.source_dirs import engine_and_world_dirs

# The only exceptions, each with the reason it is not a node reference.
ALLOWED = {
    # GOODS_CATEGORIES key: a market category that shares its name with a tree node.
    ("sim/engine/economy_goods.py", "photography"),
}
QUOTED = re.compile(r"""(["'])((?:(?!\1)[^\\\n])+)\1""")


def node_id_literals():
    """Every "file:line id" where an engine or world module has a string literal equal to a node id."""
    found = []
    for directory in engine_and_world_dirs():
        for path in sorted(glob.glob(os.path.join(directory, "**", "*.py"), recursive=True)):
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            if not any(match.group(2) in NODES for match in QUOTED.finditer(text)):
                continue
            relative = os.path.relpath(path, ROOT)
            for node in ast.walk(ast.parse(text)):
                if (isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in NODES
                        and (relative, node.value) not in ALLOWED):
                    found.append("%s:%d %s" % (relative, node.lineno, node.value))
    return found


class EngineNamesNoNodeIdTests(unittest.TestCase):
    def test_no_engine_or_world_module_names_a_technology_node_id_in_a_string_literal(self):
        self.assertEqual(node_id_literals(), [])


if __name__ == "__main__":
    unittest.main()
