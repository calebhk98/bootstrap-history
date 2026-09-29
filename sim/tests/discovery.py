"""Finds the suite's topics on disk; nothing is registered by hand.

Every sim/tests/test_*.py is a topic named by the rest of its filename, run in
sorted order. A file opts out of the default run with a module-level
`SLOW_TOPIC = True`. Kept free of heavy imports so `--list` stays instant.
"""
import ast
import os

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


def discover_topics(tests_dir=TESTS_DIR):
    """Topic names (test_<name>.py minus the affixes), sorted."""
    return sorted(filename[len("test_"):-len(".py")]
                  for filename in os.listdir(tests_dir)
                  if filename.startswith("test_") and filename.endswith(".py"))


def discover_slow_topics(tests_dir=TESTS_DIR):
    """Topics whose file sets `SLOW_TOPIC = True` at module level.

    Read from the syntax tree, so finding them imports (and runs) nothing.
    """
    slow = set()
    for name in discover_topics(tests_dir):
        path = os.path.join(tests_dir, "test_%s.py" % name)
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        if "SLOW_TOPIC" not in source:
            continue
        tree = ast.parse(source, filename=path)
        for node in tree.body:
            if (isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "SLOW_TOPIC"
                            for target in node.targets)
                    and isinstance(node.value, ast.Constant) and node.value.value is True):
                slow.add(name)
    return slow
