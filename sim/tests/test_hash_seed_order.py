"""A float sum or a tie-break must not follow the order of a set of strings, which changes with
PYTHONHASHSEED: the same inputs give the same answer under every hash seed. The check runs the
function in fresh interpreters, since a hash seed is fixed at start-up."""

QUICK_TOPIC = True

import json
import os
import subprocess
import sys

from .harness import *  # noqa: F401,F403
from .harness import ROOT

HASH_SEEDS = (0, 1, 2, 3, 4, 5, 6, 7)

# needs whose excess over the satiation limit differs by many orders of magnitude, so the freed
# spending sums to a different float in a different order
SATIATION_SCRIPT = """
import json, sys
sys.path.insert(0, %r)
from sim.world.need_satiation import apply_satiation
magnitudes = [1e16, 1.0, 3e-3, 7e8, 1e-5, 2.5e12, 9.0, 4e-9, 6e3, 1e15]
names = ["need_" + chr(97 + i) for i in range(len(magnitudes))]
units = {name: 100.0 + magnitude for name, magnitude in zip(names, magnitudes)}
units.update({"open_a": 1.0, "open_b": 2.0})
needs = {name: {"surplus_budget_share": 1.0 + index, "satiation_per_capita_per_year": 1.0}
         for index, name in enumerate(names)}
needs.update({"open_a": {"surplus_budget_share": 3.0}, "open_b": {"surplus_budget_share": 5.0}})
prices = {name: 1.0 + 0.1 * index for index, name in enumerate(sorted(units))}
apply_satiation(units, prices, needs, 1.0)
print(json.dumps([repr(units[name]) for name in sorted(units)]))
""" % ROOT


def _answer_under(hash_seed):
    return subprocess.Popen([sys.executable, "-c", SATIATION_SCRIPT], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True,
                            env=dict(os.environ, PYTHONHASHSEED=str(hash_seed)))


_processes = [_answer_under(hash_seed) for hash_seed in HASH_SEEDS]
_answers = []
for _process in _processes:
    _stdout, _stderr = _process.communicate(timeout=120)
    _answers.append(json.loads(_stdout) if _process.returncode == 0 else _stderr[-500:])

check("satiation moves freed spending to the open needs identically under every hash seed",
      all(answer == _answers[0] for answer in _answers) and isinstance(_answers[0], list),
      [answer for answer in _answers if answer != _answers[0]][:1])
