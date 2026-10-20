"""What an actor chooses to research, through its decision policy (any actor that researches).

A node is on offer when the actor knows what it rests on and values it (`Actor.research_worth`): a firm or
player by the takings of a concern it would run, a state by the gains its priorities weight. The policy picks
among the priced offers within the actor's budget; a node is never taken at a loss.
"""
from typing import Any, List

from . import business_books, research
from .player_commands import CommandRejected
from .policy import Decision, Option
from .tuning import ATTENTION_SPAN, RESEARCH_PROGRAMMES_AT_ONCE, VALUE_HORIZON_YEARS

RESEARCH_DECISION = "research"


def expected_concern_margin(actor: Any, node_id: str, world: Any) -> float:
	"""Yearly margin an operator expects from the node's concern once it has ramped up, at the economy's prices."""
	rivals = actor.rivals_of(node_id, actor.actor_id) if getattr(actor, "rivals_of", None) else 0.0
	upkeep, wages = business_books.yearly_costs(world, node_id)
	return world.entry_gross(node_id, rivals, 1.0) - upkeep - wages


def concern_worth(actor: Any, node_id: str, world: Any) -> float:
	"""What the takings of the node's concern repay over the valuing horizon (0 when it runs at a loss)."""
	return max(0.0, expected_concern_margin(actor, node_id, world)) * VALUE_HORIZON_YEARS


def options(actor: Any, world: Any, room: int = RESEARCH_PROGRAMMES_AT_ONCE, budget: float = float("inf")) -> List[Option]:
	"""The nodes worth researching, best first, priced by the shared plan until `room` of them pay within `budget`."""
	candidates = []
	for node_id in sorted(world.nodes):
		if actor.knows(node_id, world) or node_id in actor.works or research.missing_prerequisites(actor, node_id, world):
			continue
		worth = actor.research_worth(node_id, world)
		if worth > 0.0:
			candidates.append((worth, node_id))
	candidates.sort(key=lambda item: (-item[0], item[1]))
	offers: List[Option] = []
	viable = 0
	for worth, node_id in candidates[:ATTENTION_SPAN]:
		offer = Option(subject=node_id, worth=worth, cost=research.plan(actor, node_id, world)["total"],
					   chance=research.chance(node_id, world))
		offers.append(offer)
		viable += 1 if offer.net > 0.0 and offer.cost <= budget else 0
		if viable >= room:       # the best that pay are priced; the rest are not worth the evaluation
			break
	return offers


def decide(actor: Any, world: Any) -> List[str]:
	"""Ask the actor's policy which offers to take and begin them; returns the nodes begun."""
	if sum(1 for work in actor.works.values() if work.get("research")) >= RESEARCH_PROGRAMMES_AT_ONCE:
		return []
	room = RESEARCH_PROGRAMMES_AT_ONCE - sum(1 for work in actor.works.values() if work.get("research"))
	budget = actor.copy_budget(world)
	offers = options(actor, world, room, budget)
	if not offers:
		return []
	begun = []
	for option in actor.decision_policy.choose(actor, Decision(RESEARCH_DECISION, offers, budget))[:room]:
		try:
			actor.start_research(option.subject, world)
		except CommandRejected:
			continue
		begun.append(option.subject)
	return begun
