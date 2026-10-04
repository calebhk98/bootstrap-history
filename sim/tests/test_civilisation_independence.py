"""Complaints/131 and 132: no engine code names a civilisation, and the game
runs with any civilisation file absent.

Unittest style so importing it does not pull in the engine; the harness
imports the default civilisation at module load, which is the very thing
under test.
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from .source_dirs import engine_and_world_dirs

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
ROOT = os.path.dirname(SIM_DIR)
CIVILISATION_DIR = os.path.join(ROOT, "data", "civilizations")

# Offline tools that may name a civilisation, each with the reason.
TOOL_ALLOW_LIST = {
}
# The one place a default may name a civilisation: the setting itself.
ENGINE_ALLOW_LIST = {os.path.join("engine", "settings.py")}


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


SCRIPT = r'''
import os, random
from sim import simulator as S
from sim.engine import data
tree, prices, nodes, wages, goods = S.load()
goal = tree["meta"]["goal_node"]
_, order, _ = S.load_strategy("recommended", nodes, goal)
ids = sorted(name[:-5] for name in os.listdir(data.CIVDIR)
             if name.endswith(".json") and not name.startswith("_"))
assert ids and "%(hidden)s" not in ids
for civ_id in ids:
    sim = S.Sim(nodes, order, random.Random(1), events=False, manual=False,
                civ=S.load_civ(civ_id))
    sim.goal, sim.done_year = goal, {}
    sim.step()
print("ok", len(ids))
'''


class GameStartsWithoutTheDefaultCivilisation(unittest.TestCase):
    """A copy of the repository whose data directory lacks the default
    civilisation, built from symlinks so it costs nothing to make."""

    def test_game_starts_and_steps_without_the_default_civilisation_file(self):
        with open(os.path.join(SIM_DIR, "engine", "settings.py"), encoding="utf-8") as handle:
            hidden = re.search(r'"default_civ":\s*"([^"]+)"', handle.read()).group(1)
        with tempfile.TemporaryDirectory() as scratch:
            for entry in os.listdir(ROOT):
                if entry not in (".git", "data", ".claude"):
                    os.symlink(os.path.join(ROOT, entry), os.path.join(scratch, entry))
            os.mkdir(os.path.join(scratch, "data"))
            for entry in os.listdir(os.path.join(ROOT, "data")):
                if entry != "civilizations":
                    os.symlink(os.path.join(ROOT, "data", entry),
                               os.path.join(scratch, "data", entry))
            os.mkdir(os.path.join(scratch, "data", "civilizations"))
            for entry in os.listdir(CIVILISATION_DIR):
                if entry != hidden + ".json":
                    os.symlink(os.path.join(CIVILISATION_DIR, entry),
                               os.path.join(scratch, "data", "civilizations", entry))
            result = subprocess.run([sys.executable, "-c", SCRIPT % {"hidden": hidden}],
                                    cwd=scratch, env=dict(os.environ, PYTHONPATH=scratch),
                                    capture_output=True, text=True, timeout=900)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("ok", result.stdout)


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

    def test_default_civilisation_is_the_setting_when_present(self):
        from sim.engine.default_civilisation import default_civilisation_id
        from sim.engine.settings import CONFIG_DEFAULTS
        self.assertEqual(default_civilisation_id(), CONFIG_DEFAULTS["default_civ"])


if __name__ == "__main__":
    unittest.main()
