"""`Firm`: an independent business that copies a proven concern and runs it.

It values only the profit it expects from a concern it can enter, and runs
the concern under the same upkeep and takings rules as the founder's, sharing
the market with every other operator.
"""
from typing import Any, Callable, List, Optional

from . import business_books, business_review, firm_exit, research_choice
from .base import RecordedActor
from .firm_expansion import ExpansionMixin
from .borrowing import TRACK_RECORD_YEARS
from .tuning import EXIT_LOSS_YEARS, VALUE_HORIZON_YEARS


class Firm(ExpansionMixin, RecordedActor):
	kind = "firm"
	researches = True
	keeps_purchases = True   # what it buys at the market joins its stores (a state draws its purchases at once)
	borrows_for_copies = True

	# Set by the registry: how many other operators share a concern's market.
	rivals_of: Optional[Callable[[str, str], float]] = None
	# Set by the registry: told when a firm changes the size it runs a concern at.
	on_capacity_change: Optional[Callable[[str], None]] = None
	# Set by the registry: finds another actor by id (the founder whose stake the firm returns).
	find_actor: Optional[Callable[[str], Any]] = None

	def imitation_candidates(self, world: Any) -> List[str]:
		# a firm values only the concern it is aiming at
		target = self.record.target
		return [target] if target in world.demonstrated() else []

	def imitation_worth(self, node_id: str, world: Any) -> float:
		if node_id != self.record.target:
			return 0.0
		return max(0.0, self.record.last_margin) * VALUE_HORIZON_YEARS

	def research_worth(self, node_id: str, world: Any) -> float:
		"""A firm researches a node whose concern's takings, at the economy's prices, repay its cost over the horizon."""
		return research_choice.concern_worth(self, node_id, world)

	def on_copied(self, node_id: str, world: Any) -> None:
		if node_id == self.record.target:
			self.business.open_plant(node_id, world.year, self.location())

	def accept_licence(self, node_id: str, chain: List[str], world: Any) -> None:
		"""A licensed concern becomes the firm's own business."""
		self.learn(chain, world)
		self.business.open_plant(node_id, world.year, self.location())

	def operate(self, world: Any, interest: float = 0.0) -> None:
		for node_id in sorted(self.concerns):
			rivals = self.rivals_of(node_id, self.actor_id) if self.rivals_of else 0.0
			margin = (business_books.operate(self.business, self, node_id, world, rivals)
					  - business_books.carry(self.business, self, node_id, world))
			self.record.last_margin = margin
			self.business.note_year(node_id, margin)
		self.record.loss_years = self.business.longest_loss_run()
		if self.record.loss_years == 0 and self.concerns:
			weak = firm_exit.earns_less_than_plant_would_lend_for(self, world)
			self.record.weak_years = self.record.weak_years + 1 if weak else 0
			insolvent = firm_exit.interest_outruns_margin(self, interest, world)
			self.record.insolvent_years = self.record.insolvent_years + 1 if insolvent else 0

	def credit_earning(self, world: Any) -> float:
		return max(0.0, self.record.last_margin)

	def credit_standing(self, world: Any) -> float:
		"""A firm is trusted as its record lengthens, and not at all while it runs at a loss."""
		if self.record.loss_years > 0 or self.record.founded_year is None:
			return 0.0
		return min(1.0, max(0.0, world.year - self.record.founded_year) / TRACK_RECORD_YEARS)

	def default(self, world: Any) -> None:
		"""A firm in default closes: its plant is sold or scrapped to repay what it can, the rest is written off."""
		firm_exit.close_firm(self, world)
		super().default(world)

	def act(self, world: Any) -> None:
		self.prepare_bonds(world)
		interest = self.pay_interest(world)
		if self.record.exited_year is not None:
			return
		super().act(world)
		self.operate(world, interest)
		had_plants = bool(self.concerns)
		self.business.review(self, world, rules=(business_review.LOSS_MAKING,))
		if (had_plants and not self.concerns) or EXIT_LOSS_YEARS <= max(self.record.weak_years, self.record.insolvent_years):
			firm_exit.close_firm(self, world)
		else:
			self.expand(world)
