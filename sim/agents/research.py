"""Research and its diffusion, one path for every actor (a seat's player, a firm, a state).

An actor picks a node whose prerequisites it knows, pays the scholars' and craftsmen's hours and the other
costs through the labour market and its purse, and advances at its country's literacy; completion adds the
node to its own knowledge, or fails. A node some actor knows then spreads to the others over the years.
Pure functions over an actor and a world view; the actor keeps the project in `works`.
"""
import math
from typing import Any, Dict, Iterable, List

from . import imitation
from .player_commands import CommandRejected
from .tuning import HIRING_PREMIUM


def missing_prerequisites(actor: Any, node_id: str, world: Any) -> List[str]:
	return [pre for pre in world.nodes[node_id].get("pre") or () if not actor.knows(pre, world)]


def plan(actor: Any, node_id: str, world: Any) -> Dict[str, Any]:
	"""Hours, money and calendar for pioneering one node at full effort."""
	node = world.nodes[node_id]
	hours = dict(node.get("lab") or {})
	base_labour = sum(amount * world.labour_market.quote(trade, 0.0, actor) for trade, amount in hours.items())
	premium = sum(amount * world.labour_market.quote(trade, 0.0, actor) * HIRING_PREMIUM
				  for trade, amount in hours.items() if actor.workforce.get(trade, 0.0) <= 0)
	other_money = max(0.0, world.copy_cost(node_id) - base_labour)
	return {"hours": hours, "money": other_money + premium, "labour_cost": base_labour,
			"total": other_money + premium + base_labour,
			"years": max(1, int(math.ceil(float(node.get("yrs") or 0.0))))}


def chance(node_id: str, world: Any) -> float:
	return 1.0 - min(1.0, world.copy_risk(node_id))


def begin(actor: Any, node_id: str, world: Any) -> str:
	"""Begin researching a node; refuses with the reason."""
	if node_id not in world.nodes:
		raise CommandRejected("no such node")
	if actor.knows(node_id, world):
		raise CommandRejected("already known")
	if node_id in actor.works:
		raise CommandRejected("already being researched")
	missing = missing_prerequisites(actor, node_id, world)
	if missing:
		raise CommandRejected("prerequisites unknown: " + ", ".join(sorted(missing)))
	costs = plan(actor, node_id, world)
	if costs["total"] > actor.copy_budget(world):
		raise CommandRejected("cannot afford the research")
	work = imitation.start_work(node_id, [node_id], costs, world.year)
	work["research"] = True
	actor.works[node_id] = work
	return "research begun, %d years" % costs["years"]


def work_year(actor: Any, world: Any) -> List[str]:
	"""Advance every research a year at the country's literacy (the caller has cleared last year's staff);
	returns the nodes learned."""
	learned = []
	for node_id in sorted(actor.works):
		work = actor.works[node_id]
		if not work.get("research"):
			continue
		if not imitation.work_year(actor, node_id, work, world, world.research_productivity()):
			continue
		del actor.works[node_id]
		roll = world.rng_for(world.year, actor.kind, node_id, actor.identity())
		if roll.random() < chance(node_id, world):
			actor.learn([node_id], world)
			learned.append(node_id)
		else:
			actor.record_failure(node_id)
	return learned


def diffuse(actors: Iterable[Any], world: Any) -> List[str]:
	"""One year of knowledge spreading between actors: an actor that lacks a node some other actor knows, and
	knows what it rests on, learns it with the yearly share the half-life leaves, scaled by how much of it the
	holder shows at the learner's distance. Returns "learner:node" for each learning, in order."""
	ordered = sorted(actors, key=lambda actor: actor.identity())
	known = sorted({node for actor in ordered for node in actor.knowledge} - world.baseline_knowledge())
	if not known:
		return []
	hazard = 1.0 - 0.5 ** (1.0 / max(1e-9, world.knowledge_half_life_years()))
	learned = []
	for node_id in known:
		if node_id not in world.nodes:
			continue
		holders = [actor for actor in ordered if node_id in actor.knowledge]
		for learner in ordered:
			if learner.knows(node_id, world) or missing_prerequisites(learner, node_id, world):
				continue
			roll = world.rng_for(world.year, "diffusion", node_id, learner.identity()).random()
			if roll >= hazard:
				continue
			seen = max(world.knowledge_visibility(node_id, world.distance_km(holder.location(), learner.location()))
					   for holder in holders)
			if roll < hazard * seen:
				learner.learn([node_id], world)
				learned.append("%s:%s" % (learner.identity(), node_id))
	return learned
