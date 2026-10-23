"""Complaints/131 and 132: no engine code names a civilisation, and whether an institution is foreign follows the
society tag. Source scans and a pure function, no game. The game starting with a civilisation file absent is in
test_civilisation_independence."""
QUICK_TOPIC = True

import os
import re
import unittest
from .source_dirs import engine_and_world_dirs

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
ROOT = os.path.dirname(SIM_DIR)
CIVILISATION_DIR = os.path.join(ROOT, "data", "civilizations")

# Offline tools that may name a civilisation, each with the reason.
TOOL_ALLOW_LIST = {
    "default_civilisation.py": "holds the default-civilisation setting, shared by the engine and labour",
}
# Nothing in the engine or world may name one; the default setting lives in sim/default_civilisation.py.
ENGINE_ALLOW_LIST = set()


def civilisation_ids():
    return sorted(name[:-5] for name in os.listdir(CIVILISATION_DIR)
                  if name.endswith(".json") and not name.startswith("_"))


def python_files(directory, recursive):
    for folder, subfolders, names in os.walk(directory):
        subfolders[:] = [name for name in subfolders
                         if name not in ("tests", "__pycache__")]
        for name in names:
            if name.endswith(".py"):
                yield os.path.join(folder, name)
        if not recursive:
            break


def mentions(path, pattern):
    with open(path, encoding="utf-8") as handle:
        return [(number, line.strip()) for number, line in enumerate(handle, 1)
                if pattern.search(line)]


class NoCivilisationIdInCode(unittest.TestCase):
    def pattern(self):
        return re.compile("|".join(re.escape(civ) for civ in civilisation_ids()))

    def test_engine_and_world_name_no_civilisation(self):
        pattern = self.pattern()
        found = []
        for directory in engine_and_world_dirs():
            for path in python_files(directory, True):
                if os.path.relpath(path, SIM_DIR) in ENGINE_ALLOW_LIST:
                    continue
                found += [(os.path.relpath(path, SIM_DIR), number, text)
                          for number, text in mentions(path, pattern)]
        self.assertEqual(found, [])

    def test_top_level_tools_name_no_civilisation_unless_justified(self):
        pattern = self.pattern()
        found = []
        for path in python_files(SIM_DIR, False):
            if os.path.basename(path) in TOOL_ALLOW_LIST:
                continue
            found += [(os.path.basename(path), number, text)
                      for number, text in mentions(path, pattern)]
        self.assertEqual(found, [])


class ForeignInstitutionsFollowData(unittest.TestCase):
    """Whether an institution is foreign comes from the civilisation's society
    tag and the marker table, not from which civilisation it is."""

    def test_foreignness_follows_the_society_tag(self):
        from sim.engine import institution_societies as societies
        text = "annona_grain_dole"
        owner = societies._table()["markers"]["annona"]
        self.assertFalse(societies.belongs_to_other_society(text, {"id": owner}, "markers"))
        self.assertTrue(societies.belongs_to_other_society(text, {"id": "invented"}, "markers"))
        self.assertFalse(societies.belongs_to_other_society(
            text, {"id": "invented", "society": owner}, "markers"))
        self.assertTrue(societies.belongs_to_other_society(
            text, {"id": owner, "society": "invented"}, "markers"))


if __name__ == "__main__":
    unittest.main()
