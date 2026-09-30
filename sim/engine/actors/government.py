"""`Government`: a country's state as an actor.

It values inventions by the gains its civilisation's priorities weight
(military, infrastructure, prestige, ...), funds copying from a share of the
revenue it raises, and acts through its policy.
"""
from typing import Any

from .base import RecordedActor
from .tuning import GOVERNMENT_DISCRETIONARY_SHARE, GOVERNMENT_WORTH_SHARE_PER_GAIN
from .values import invention_gains, weighted_gain


class Government(RecordedActor):
	kind = "government"

	def imitation_worth(self, node_id: str, world: Any) -> float:
		gains = invention_gains(world.nodes[node_id])
		gain = weighted_gain(gains, world.state_weights())
		return max(0.0, gain) * world.state_revenue() * GOVERNMENT_WORTH_SHARE_PER_GAIN

	def advance(self, world: Any) -> None:
		self.credit(world.state_revenue() * GOVERNMENT_DISCRETIONARY_SHARE, "taxation")
		super().advance(world)
