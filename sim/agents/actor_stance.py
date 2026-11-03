"""`ActorStance`: how an actor answers the state's demands, and how prominent it is. Reached as `actor.stance`.

The default suits an actor with no standing to speak of; `RecordedStance` keeps the answers on the actor's record.
"""
from typing import Any


class ActorStance:

	def __init__(self, actor: Any) -> None:
		self.actor = actor

	def prominence(self) -> float:
		"""How prominent the actor is as a person; a business has none."""
		return 0.0

	def standing(self) -> float:
		"""Standing and patronage that bargain a levy down, 0..1."""
		return 0.0

	def demand_stance(self) -> str:
		"""How the actor answers the state's demands: comply unless it has said otherwise."""
		return "comply"

	def set_demand_stance(self, stance: str) -> None:
		"""Answer the state's demands from now on with `stance`."""
		raise NotImplementedError

	def service_worth(self) -> float:
		"""Money's worth of service the actor will offer the state in place of part of a demand."""
		return 0.0

	def concealed_wealth(self) -> float:
		"""Wealth the actor holds where the state cannot count it."""
		return 0.0

	def defiance(self) -> float:
		"""0..1: how far the state holds the actor's refusals against it."""
		return 0.0

	def set_concealed_wealth(self, amount: float) -> None:
		"""Hold `amount` of its wealth out of the state's sight."""

	def set_defiance(self, level: float) -> None:
		"""The state now holds the actor's defiance at `level`."""


class RecordedStance(ActorStance):

	def demand_stance(self) -> str:
		return self.actor.record.demand_stance

	def set_demand_stance(self, stance: str) -> None:
		self.actor.record.demand_stance = stance

	def service_worth(self) -> float:
		return self.actor.record.service_offer

	def concealed_wealth(self) -> float:
		return self.actor.record.concealed

	def defiance(self) -> float:
		return self.actor.record.defiance

	def set_concealed_wealth(self, amount: float) -> None:
		self.actor.record.concealed = max(0.0, amount)

	def set_defiance(self, level: float) -> None:
		self.actor.record.defiance = level
