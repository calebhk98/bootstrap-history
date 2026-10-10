"""The year's turn of an actor's answer to the state: hiding wealth, and the state's memory of a refusal.

Concealed wealth is the actor's own money held where the state cannot count it (`demand_answer.visible_wealth`):
it costs a share a year to keep there, and a state that finds it takes it with a penalty in proportion to its
capacity. A state forgets a refusal slowly. Run once a year for every actor that has something to settle.
"""
from typing import Any, Dict, List

from . import demand_answer, ledger
from .edges import EDGE_OFFICIALS
from .registry import register_spawner


def settle_year(actor: Any, world: Any) -> Dict[str, float]:
	"""One year of concealment and forgetting for `actor`; what was hidden, what hiding cost, what the state seized."""
	stance = actor.demand_stance()
	settled = {"concealed": 0.0, "cost": 0.0, "seized": 0.0, "found": 0.0}
	if stance == demand_answer.CONCEAL or actor.concealed_wealth() > 0.0:
		draw = world.rng_for("conceal", actor.actor_id, world.year).random()
		settled = demand_answer.settle_concealment(stance, max(0.0, actor.money), world.state_capacity(),
												   actor.standing(), draw)
		if settled["cost"] > 0.0:
			ledger.transfer(actor, world.edge(EDGE_OFFICIALS), settled["cost"], "concealing wealth")
		if settled["seized"] > 0.0:
			ledger.transfer(actor, world.government(), settled["seized"], "wealth found hidden")
		actor.set_concealed_wealth(settled["concealed"])
	if actor.defiance() > 0.0:
		actor.set_defiance(demand_answer.defiance_fading(actor.defiance()))
	return settled


def settle_all(registry: Any, world: Any) -> List[str]:
	"""Every actor that has hidden wealth, holds a stance that hides it, or carries the state's memory of a refusal."""
	settled = []
	for actor_id in sorted(registry.actors):
		actor = registry.actors[actor_id]
		if actor.record.exited_year is not None or actor.kind == "government":
			continue
		if actor.demand_stance() == demand_answer.CONCEAL or actor.concealed_wealth() > 0.0 or actor.defiance() > 0.0:
			settle_year(actor, registry.world_for(actor, world))
			settled.append(actor_id)
	return settled


register_spawner("demand_year", settle_all)
