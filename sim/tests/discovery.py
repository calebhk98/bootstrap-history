"""Finds the suite's topics on disk; nothing is registered by hand.

Every sim/tests/test_*.py is a topic named by the rest of its filename, run in
sorted order. A file joins the quick tier (the default run) with a module-level
`QUICK_TOPIC = True`, and leaves the parallel batch with
`SERIAL_TOPIC = True`. A topic whose subject is a long run by design may set a module-level
`TOPIC_SECONDS = <number>` (with a comment naming why and what retires it): the runner lets that topic run that
long instead of the default limit, and never batches it with others. Kept free of heavy imports so `--list` stays instant.
"""
import ast
import os

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


def discover_topics(tests_dir=TESTS_DIR):
    """Topic names (test_<name>.py minus the affixes), sorted."""
    return sorted(filename[len("test_"):-len(".py")]
                  for filename in os.listdir(tests_dir)
                  if filename.startswith("test_") and filename.endswith(".py"))


def discover_quick_topics(tests_dir=TESTS_DIR):
    """Topics whose file sets `QUICK_TOPIC = True` at module level: the default run."""
    return _discover_flag("QUICK_TOPIC", tests_dir)


def discover_serial_topics(tests_dir=TESTS_DIR):
    """Topics whose file sets `SERIAL_TOPIC = True`: never run beside another topic."""
    return _discover_flag("SERIAL_TOPIC", tests_dir)


def discover_topic_allowances(tests_dir=TESTS_DIR):
    """{topic: seconds} for topics whose file sets `TOPIC_SECONDS = <number>` at module level."""
    found = {}
    for name in discover_topics(tests_dir):
        path = os.path.join(tests_dir, "test_%s.py" % name)
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        if "TOPIC_SECONDS" not in source:
            continue
        for node in ast.parse(source, filename=path).body:
            if (isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "TOPIC_SECONDS" for target in node.targets)
                    and isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float))):
                found[name] = float(node.value.value)
    return found


def _discover_flag(flag, tests_dir):
    """Topics whose file sets `<flag> = True` at module level.

    Read from the syntax tree, so finding them imports (and runs) nothing.
    """
    found = set()
    for name in discover_topics(tests_dir):
        path = os.path.join(tests_dir, "test_%s.py" % name)
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        if flag not in source:
            continue
        tree = ast.parse(source, filename=path)
        for node in tree.body:
            if (isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == flag
                            for target in node.targets)
                    and isinstance(node.value, ast.Constant) and node.value.value is True):
                found.add(name)
    return found
