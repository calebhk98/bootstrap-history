"""Rome's opening states the enslaved share as an initial condition: a bonded stratum held by the rich."""
import random

from .harness import *  # noqa: F401,F403

SLAVE_SHARE = 0.1  # the sourced empire-wide share in data/civilizations/rome_100ad.json (Scheidel 2005)

civ = S.load_civ("rome_100ad")
declared = civ["cast"]["strata"]
check("Rome declares its strata", len(declared) >= 2, declared)
check("the declared shares add up to every person", abs(sum(entry["share"] for entry in declared) - 1.0) < 1e-9,
      sum(entry["share"] for entry in declared))
check("the enslaved share carries its source and confidence",
      civ["_internal"]["cast"]["source"] and civ["_internal"]["cast"]["confidence"] in "ABCD")

game = S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=civ, cfg={"agent_economy": False})
for _ in range(2):  # the first year only seeds the roster
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)
registry = game.actors
home_strata = [actor for actor in registry.of_kind("stratum") if actor.record.country is None]
bonded = [actor for actor in home_strata if actor.is_bonded()]
check("Rome's opening has exactly one bonded stratum", len(bonded) == 1, [actor.actor_id for actor in bonded])
slaves = bonded[0]
people = sum(actor.record.members for actor in home_strata)
check("the bonded stratum holds the sourced share of the people",
      abs(slaves.record.members / people - SLAVE_SHARE) < 0.01, slaves.record.members / people)
check("the bonded are kept by a stratum that exists",
      registry.actors.get(slaves.neighbour_id(slaves.record.plan["owner"])) is not None, slaves.record.plan)
check("the bonded eat from their owner's keep", slaves.record.income.get("keep of bonded", 0.0) > 0.0,
      slaves.record.income)
check("the free strata still earn",
      all(actor.record.income.get("edge:economy", 0.0) > 0.0
          for actor in home_strata if not actor.is_bonded() and actor.record.stratum != "poor"))
owner = registry.actors[slaves.neighbour_id(slaves.record.plan["owner"])]
check("the owner stratum is not run down by the keep: its net money is positive", owner.money > 0.0, owner.money)
