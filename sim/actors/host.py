"""What `ActorWorld` asks of the actors module besides its views: the six answers it calls on its host, from the parts that give them.

A seam kept until `ActorWorld` is handed the parts it asks (Complaint 964); nothing else asks the host."""
from typing import Any


class WorldHost:

	def __init__(self, module: Any) -> None:
		self.module = module
		self.needs = module.needs

	def cast(self) -> Any:
		return self.module.parts.cast.cast()

	def edge(self, name: str) -> Any:
		return self.module.parts.cast.edge(name)

	def state_treasury(self) -> Any:
		return self.module.parts.cast.state_treasury()

	def seat_parties(self) -> Any:
		return self.module.parts.seat_parties.seat_parties()

	def seat_party(self, seat_id: str) -> Any:
		return self.module.parts.seat_parties.seat_party(seat_id)

	def actor_concerns_in(self, category: str) -> float:
		return self.module.parts.staff.actor_concerns_in(category)
