"""`ActorCopying`: an actor's yearly work on copying inventions and on research. Reached as `actor.copying`.

The hooks it calls stay on the actor so a kind can override them: `imitation_worth`, `imitation_candidates`, `copy_budget`,
`learn`, `on_copied`, `record_failure`, `research_worth`, `research_price`, `commit_research`.
"""
from typing import Any, List

from . import awareness, imitation, research
from .policy import Decision, Option
from .tuning import ATTENTION_SPAN


class ActorCopying:

	def __init__(self, actor: Any) -> None:
		self.actor = actor

	def imitation_options(self, world: Any) -> List[Option]:
		"""Priced options for the inventions that look most worth copying."""
		candidates = []
		known = self.actor.knowledge
		baseline = world.knowledge.baseline_knowledge()
		for node_id in self.actor.imitation_candidates(world):
			if node_id in known or node_id in baseline or node_id in self.actor.works \
					or not awareness.knows_it_exists(self.actor, node_id, world):
				continue
			worth = self.actor.imitation_worth(node_id, world)
			if worth > 0 and imitation.in_sight(self.actor.location(), node_id, world):
				candidates.append((worth * world.knowledge.exposure(node_id, self.actor.location()), node_id))
		candidates.sort(key=lambda item: (-item[0], item[1]))
		options = []
		for worth, node_id in candidates[:ATTENTION_SPAN]:
			chain = imitation.missing_chain(node_id, world, self.actor)
			if not chain:
				continue
			plan = imitation.copy_plan(self.actor, chain, world)
			options.append(Option(subject=node_id, worth=worth, cost=plan["total"],
								  chance=imitation.copy_chance(chain, world),
								  detail={"chain": chain, "plan": plan}))
		return options

	def consider_imitation(self, world: Any) -> List[str]:
		"""Ask the policy which invention to copy, and begin those copies."""
		options = self.imitation_options(world)
		if not options:
			return []
		decision = Decision("imitate", options, self.actor.copy_budget(world))
		begun = []
		for option in self.actor.decision_policy.choose(self.actor, decision):
			detail = option.detail
			self.actor.works[option.subject] = imitation.start_work(
				option.subject, detail["chain"], detail["plan"], world.setting.year)
			begun.append(option.subject)
		return begun

	def work_on_copies(self, world: Any) -> List[str]:
		"""Advance every copy a year; returns the ids that succeeded (its crew is what the labour core hired, kept as it is)."""
		finished = []
		for node_id in sorted(self.actor.works):
			work = self.actor.works[node_id]
			if work.get("research"):
				continue
			if not imitation.work_year(self.actor, node_id, work, world):
				continue
			del self.actor.works[node_id]
			roll = world.setting.rng_for(world.setting.year, self.actor.kind, node_id, self.actor.identity())
			if roll.random() < imitation.copy_chance(work["chain"], world):
				self.actor.learn(work["chain"], world)
				self.actor.on_copied(node_id, world)
				finished.append(node_id)
			else:
				self.actor.record_failure(node_id)
		return finished

	def start_research(self, node_id: str, world: Any) -> str:
		"""Begin researching a node (any actor, one path: `research.py`); refuses with the reason."""
		return research.begin(self.actor, node_id, world)

	def work_on_research(self, world: Any) -> List[str]:
		"""Advance every research a year at the country's literacy; returns the nodes learned."""
		return research.work_year(self.actor, world)
