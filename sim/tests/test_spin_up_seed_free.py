"""The agent economy's hidden spin-up draws nothing from the game's seed: the economy package holds no random source
(Complaints/closed/400). The opening it is cached on being the same for every seed is
test_spin_up_seed_free_scenario."""

QUICK_TOPIC = True

import glob
import os

from .harness import HERE, check

ECONOMY_DIRECTORY = os.path.join(HERE, "economy")

paths = glob.glob(os.path.join(ECONOMY_DIRECTORY, "*.py"))
check("the economy package is found to be read", len(paths) > 10, len(paths))
sources = {}
for path in paths:
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if "import random" in text or "from random" in text or "numpy.random" in text:
        sources[os.path.basename(path)] = True
check("the economy package imports no random source", not sources, sorted(sources))
