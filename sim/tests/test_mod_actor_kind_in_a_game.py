"""A declared kind named in a civilisation's cast takes part in a real game's actor years.

Slow topic: it builds a whole game (not in the quick tier)."""
import random

from .harness import *  # noqa: F401,F403

from sim.agents.api import register_declared_kinds

KIND = "test_acme_k3f9:elf"
register_declared_kinds({KIND: {"needs": {"food": 1.0}, "birth_rate": 0.04, "death_rate": 0.02,
                                 "famine_death_rate": 0.3, "trade": "labourer"}})
civ = dict(S.load_civ("rome_100ad"))
civ["cast"] = dict(civ.get("cast") or {}, actors=[
    {"actor_id": "elves:one", "kind": KIND, "name": "elves", "params": {"members": 500.0}}])
GAME = S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=civ)
for _ in range(3):
    GAME.state.scenario.year += 1
    GAME.advance_actors(GAME.state.scenario.year)
elves = GAME.actors.get("elves:one")
check("the declared kind is created from the cast", elves is not None and elves.kind == KIND)
check("it takes its yearly turn and its headcount moves", elves.record.members != 500.0, elves.record.members)
check("its needs were priced by the ordinary market", "food" in elves.record.shortfall, elves.record.shortfall)
