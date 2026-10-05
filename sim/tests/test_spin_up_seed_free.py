"""The agent economy's hidden spin-up draws nothing from the game's seed: the economy package holds no random
source and the opening the spin-up is cached on is the same for every seed. A median over seeds therefore
samples what happens after the spin-up, and the spin-up is one fixed starting point (Complaints/closed/400)."""
import glob
import json
import os
import random

from .harness import *  # noqa: F401,F403

from sim.engine.economy_port_setup import opening_values

ECONOMY_DIRECTORY = os.path.join(HERE, "economy")

sources = {}
for path in glob.glob(os.path.join(ECONOMY_DIRECTORY, "*.py")):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if "import random" in text or "from random" in text or "numpy.random" in text:
        sources[os.path.basename(path)] = True
check("the economy package imports no random source", not sources, sorted(sources))

openings = []
for seed in (1, 2, 7):
    game = S.Sim(NODES, ORDER, random.Random(seed), events=False, manual=True, civ=S.load_civ("norse_900ad"))
    openings.append(json.dumps(opening_values(game), sort_keys=True))
check("every seed opens the same economy, so the spin-up cache key is shared", len(set(openings)) == 1)
