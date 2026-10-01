"""`Government`: a country's state as an actor.

It values inventions by the gains its civilisation's priorities weight
(military, infrastructure, prestige, ...), funds copying from a share of the
revenue it raises, and acts through its policy.
"""
from typing import Any, Dict, Tuple

from . import ledger
from .base import Actor, RecordedActor
from .tuning import GOVERNMENT_DISCRETIONARY_SHARE, GOVERNMENT_WORTH_SHARE_PER_GAIN
from .values import invention_gains, weighted_gain


class Government(RecordedActor):
	kind = "government"

	def imitation_worth(self, node_id: str, world: Any) -> float:
		gains = invention_gains(world.nodes[node_id])
		gain = weighted_gain(gains, world.state_weights())
		return max(0.0, gain) * world.state_revenue() * GOVERNMENT_WORTH_SHARE_PER_GAIN

	def assess(self, payer: Actor, taxable: float, world: Any) -> Tuple[float, Dict[str, float]]:
		"""What the state levies on `payer` from `taxable` income this year, by purpose.

		One rule for every taxpayer: the state sees a visible scale (staff, wealth,
		prominence), and its capacity and the civilisation's shares set the rate.
		"""
		requisition, office = world.levy_shares(world.visible_scale_of(payer), payer.standing())
		parts = {"requisition": requisition * max(0.0, taxable), "office": office * max(0.0, taxable)}
		return sum(parts.values()), parts

	def collect(self, payer: Actor, taxable: float, world: Any) -> float:
		"""Levy `payer` and receive it; the amount taken."""
		levy, parts = self.assess(payer, taxable, world)
		if levy > 0.0:
			ledger.transfer(payer, self, levy, parts)
		return levy

	def advance(self, world: Any) -> None:
		self.credit(world.state_revenue() * GOVERNMENT_DISCRETIONARY_SHARE, "taxation")
		super().advance(world)
