"""Awareness: an actor can adopt only what it knows exists, and it comes to know through contact.

Contact is whatever carries news of a technique from a holder to an onlooker: trade partners on routes,
neighbours, migrants and conquests (recorded as contact events on the receiver), and a founder's working
demonstration. Each year an actor that lacks a technique and is not yet aware of it becomes aware with a
chance that rises with the contact volume it has with those who hold it. Awareness grants no skill: the
actor must still copy or research the node. Pure functions over actors and a world view.
"""
import math
from typing import Any, Iterable, List

from .tuning_adoption import (AWARENESS_RATE_PER_CONTACT, CONTACT_FADE_PER_YEAR, DEMONSTRATION_VOLUME)

NO_PLACE = ""


def hazard(volume: float) -> float:
	"""Chance in a year of learning that a technique exists, from the contact volume with its holders."""
	return 1.0 - math.exp(-AWARENESS_RATE_PER_CONTACT * max(0.0, volume))


def knows_it_exists(actor: Any, node_id: str, world: Any) -> bool:
	"""Whether the actor may take the node up. A node no one has shown anywhere is open to pioneering, and an
	actor that keeps no awareness (a seat) or takes no part in knowledge spreading sees everything."""
	aware = getattr(actor, "aware", None)
	if aware is None or not getattr(actor, "researches", False) or node_id in aware or actor.knows(node_id, world):
		return True
	return node_id not in world.demonstrated()


def record_contact(actor: Any, source_place: Any, volume: float) -> None:
	"""A new route, a conquest or a migration from `source_place` raises the receiving actor's contact with it."""
	if volume <= 0.0:
		return
	key = NO_PLACE if source_place is None else str(source_place)
	actor.contacts[key] = actor.contacts.get(key, 0.0) + volume


def fade_contacts(actor: Any) -> None:
	for key in sorted(actor.contacts):
		actor.contacts[key] *= CONTACT_FADE_PER_YEAR
		if actor.contacts[key] < 1e-6:
			del actor.contacts[key]


def volume_with(learner: Any, holders: Iterable[Any], world: Any) -> float:
	"""Contact volume between the learner and the holders: the world's reading of the two places plus events."""
	total = 0.0
	for holder in holders:
		place = holder.location()
		total += float(world.contact_volume(holder.location(), learner.location()))
		total += learner.contacts.get(NO_PLACE if place is None else str(place), 0.0)
	return total


def spread(actors: Iterable[Any], world: Any) -> List[str]:
	"""One year of news: each actor that lacks a shown node and is not aware of it may become aware.
	Returns "actor:node" for each new awareness, in order. Contact events fade after being counted."""
	ordered = sorted(actors, key=lambda actor: actor.identity())
	demonstrated = world.demonstrated() if hasattr(world, "demonstrated") else set()
	held = {node_id for actor in ordered for node_id in actor.knowledge}
	shown = sorted((demonstrated | held) - world.baseline_knowledge())
	found = []
	for node_id in shown:
		holders = [actor for actor in ordered if node_id in actor.knowledge]
		for learner in ordered:
			if learner.knows(node_id, world) or node_id in learner.aware:
				continue
			volume = volume_with(learner, [holder for holder in holders if holder is not learner], world)
			volume += DEMONSTRATION_VOLUME * float(world.exposure(node_id, learner.location()))
			roll = world.rng_for(world.year, "awareness", node_id, learner.identity()).random()
			if roll < hazard(volume):
				learner.aware[node_id] = world.year
				found.append("%s:%s" % (learner.identity(), node_id))
	for learner in ordered:
		fade_contacts(learner)
	return found
