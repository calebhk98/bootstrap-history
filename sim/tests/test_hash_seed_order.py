"""A float sum or a tie-break must not follow the order of a set of strings, which changes with
PYTHONHASHSEED: the same inputs give the same answer under every hash seed. The check runs the
function in fresh interpreters, since a hash seed is fixed at start-up."""

QUICK_TOPIC = True

# The slow check opens two games from a fresh cache under two hash seeds, which is two whole openings and spin-ups
# side by side; nothing shorter checks the opening's order. Measure with `--slow --only hash_seed_order`.
TOPIC_SECONDS = 360

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

# The opening years of the agent economy are cached on disk, so the usual two-seed run (see
# run_reproducibility) replays whichever spin-up a process first computed and never exercises them.
# Here the cache is a fresh directory and the spin-up is long enough for cohorts to reach their
# satiation limits (re-measure by finding the first year two hash seeds' records differ).
SPIN_UP_YEARS = "6,0"
SPIN_UP_SCRIPT = """
import hashlib, json, sys, tempfile
sys.path.insert(0, %r)
from sim.tests.harness import sim
from sim.engine import economy_port_year
economy_port_year.SPIN_UP_CACHE_DIRECTORY = tempfile.mkdtemp()
game = sim()
record = game.economy.agent.stored["record"]
print(hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest())
""" % ROOT


def _spin_up_under(hash_seed):
    return subprocess.Popen([sys.executable, "-c", SPIN_UP_SCRIPT], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True,
                            env=dict(os.environ, PYTHONHASHSEED=str(hash_seed), ROME_SPIN_UP_YEARS=SPIN_UP_YEARS))


_spin_ups = [_spin_up_under(hash_seed) for hash_seed in (1, 2)] if SLOW else []


def _same_spin_up_under_other_hash_seed():
    digests = []
    for process in _spin_ups:
        stdout, stderr = process.communicate(timeout=600)
        if process.returncode != 0:
            raise RuntimeError("spin-up subprocess failed: %s" % stderr[-2000:])
        digests.append(stdout.strip())
    return digests[0] == digests[1], digests


slow_check("a fresh spin-up gives the same economy under another string hash seed",
           _same_spin_up_under_other_hash_seed)
