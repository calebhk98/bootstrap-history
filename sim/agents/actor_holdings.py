"""`ActorHoldings`: the books an actor keeps on the concerns it runs. Reached as `party.holdings` for any party to an exchange.

The default suits an actor that tracks no single concern; `RecordedHoldings` reads the actor's business.
"""
from typing import Any, Optional

from .business_closing import release_plant
from .business_plant import Plant


class ActorHoldings:

	def __init__(self, actor: Any) -> None:
		self.actor = actor

	def opened_year_of(self, node_id: str, default: int) -> int:
		"""When the actor began running a concern."""
		return default

	def staffed_share(self, node_id: str) -> float:
		"""Share of a concern's staff the actor has found."""
		return 1.0

	def capacity_of(self, node_id: str) -> float:
		"""How many times its founding size the actor runs a concern at."""
		return 1.0

	def margin_of(self, node_id: str) -> Optional[float]:
		"""What a concern made last year, or None when the actor does not track it singly."""
		return None

	def concern_count(self) -> int:
		return len(self.actor.concerns)

	def release_plant(self, node_id: str, world: Any) -> Plant:
		"""Stop running a concern and hand over its plant, to be taken up by another actor."""
		raise NotImplementedError

	def receive_plant(self, plant: Plant, world: Any) -> None:
		"""Take up a plant another actor handed over."""
		raise NotImplementedError


class RecordedHoldings(ActorHoldings):

	def opened_year_of(self, node_id: str, default: int) -> int:
		return self.actor.record.business.reading.opened_year_of(node_id, default)

	def staffed_share(self, node_id: str) -> float:
		return self.actor.record.business.reading.crew_found_of(node_id)

	def capacity_of(self, node_id: str) -> float:
		return self.actor.record.business.reading.size_of(node_id)

	def margin_of(self, node_id: str) -> Optional[float]:
		return self.actor.record.business.reading.margin_of(node_id)

	def release_plant(self, node_id: str, world: Any) -> Plant:
		return release_plant(self.actor.record.business, node_id, world)

	def receive_plant(self, plant: Plant, world: Any) -> None:
		self.actor.record.business.lifecycle.adopt(plant)
