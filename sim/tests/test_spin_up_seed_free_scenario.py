"""Scenario for Complaints/closed/400: the opening the agent economy's spin-up is cached on is the same for every seed, so a
median over seeds samples what happens after the spin-up. That the economy package holds no random source is
test_spin_up_seed_free."""
import json
import random

from .harness import *  # noqa: F401,F403

from sim.engine.economy_port_setup import opening_values

openings = []
for seed in (1, 2, 7):
    game = S.Sim(NODES, ORDER, random.Random(seed), events=False, manual=True, civ=S.load_civ("norse_900ad"))
    openings.append(json.dumps(opening_values(game), sort_keys=True))
check("every seed opens the same economy, so the spin-up cache key is shared", len(set(openings)) == 1)
