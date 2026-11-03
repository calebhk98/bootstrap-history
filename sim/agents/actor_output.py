"""`ActorOutput`: what an actor's concerns put on the market. Reached as `actor.output`."""
from typing import Any, List, Tuple


class ActorOutput:

	def __init__(self, actor: Any) -> None:
		self.actor = actor

	def output_by_concern(self, material: str, world: Any) -> List[Tuple[str, float]]:
		"""[(node id, tonnes a year)] of `material` each of the actor's concerns puts on the market."""
		makers = world.enterprises.concerns_making(material)
		return [(node_id, world.concerns.concern_output_tonnes(node_id, material,
													  self.actor.opened_year_of(node_id, world.setting.year),
													  self.actor.staffed_share(node_id) * self.actor.capacity_of(node_id)))
				for node_id in sorted(node_id for node_id in self.actor.concerns if node_id in makers)]

	def output_of(self, material: str, world: Any) -> float:
		"""Tonnes a year of `material` the actor's concerns put on the market."""
		return sum(tonnes for _node_id, tonnes in self.output_by_concern(material, world))
