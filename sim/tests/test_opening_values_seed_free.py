"""Complaints/closed/400: the opening the agent economy's spin-up is cached on is the same for every seed, so the modules
that build it (`opening_values` and the costs and partners it reads) draw on no random source and read no game rng. That the
economy package itself holds none is test_spin_up_seed_free."""

QUICK_TOPIC = True

import os
import re

from .harness import HERE, check

ENGINE_DIRECTORY = os.path.join(HERE, "engine")
OPENING_MODULES = ("economy_port_setup.py", "economy_port_costs.py", "economy_port_partners.py")
RANDOM_SOURCE = re.compile(r"\brandom\b|\brng\b|\bseed\b")

found = {}
for module in OPENING_MODULES:
    with open(os.path.join(ENGINE_DIRECTORY, module), encoding="utf-8") as handle:
        text = handle.read()
    found[module] = sorted(set(RANDOM_SOURCE.findall(text)))
check("the modules that build the opening are read", all(os.path.getsize(os.path.join(ENGINE_DIRECTORY, module)) > 500
                                                          for module in OPENING_MODULES))
check("none of them names a random source, a game rng or a seed", not any(found.values()), found)
