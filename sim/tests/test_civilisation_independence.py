"""Complaints/131 and 132: the game runs with any civilisation file absent. The source scans that no engine code names a
civilisation are in test_civilisation_independence_scans.

Unittest style so importing it does not pull in the engine; the harness imports the default civilisation at module
load, which is the very thing under test.
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
ROOT = os.path.dirname(SIM_DIR)
CIVILISATION_DIR = os.path.join(ROOT, "data", "civilizations")

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
    S.load_civ(civ_id)
sim = S.Sim(nodes, order, random.Random(1), events=False, manual=False,
            civ=S.load_civ(ids[0]))
sim.goal, sim.done_year = goal, {}
sim.step()
print("ok", len(ids))
'''


class GameStartsWithoutTheDefaultCivilisation(unittest.TestCase):
    """A copy of the repository whose data directory lacks the default
    civilisation, built from symlinks so it costs nothing to make."""

    def test_game_starts_and_steps_without_the_default_civilisation_file(self):
        with open(os.path.join(SIM_DIR, "default_civilisation.py"), encoding="utf-8") as handle:
            hidden = re.search(r'PREFERRED_DEFAULT_CIVILISATION = "([^"]+)"', handle.read()).group(1)
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


if __name__ == "__main__":
    unittest.main()
