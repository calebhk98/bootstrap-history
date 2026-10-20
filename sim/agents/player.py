"""`Player`: a second (third, ...) player in the same game, human, LLM or AI.

It has its own purse, research tree, staff, concerns and works. Like the founder it comes from the
future, so it may research any node whose prerequisites it knows, not only what someone showed it.
A human or LLM player acts only through queued orders (`player_commands.py`) and runs what it owns;
an AI player also decides for itself.
"""
import math
from typing import Any, Callable, List, Optional

from . import business_books, ledger, research, research_choice
from .base import RecordedActor
from .player_commands import CommandRejected, run_orders
from .registry import register_actor_kind
from .tuning_player import PLAYER_VISIBLE_EXPOSURE


class Player(RecordedActor):
	kind = "player"
	researches = True

	# Set by the registry: how many other operators share a concern's market.
	rivals_of: Optional[Callable[[str, str], float]] = None
	# Set by the registry: the actor with an id, or None; how a payment finds its payee.
	find_actor: Optional[Callable[[str], Any]] = None

	def imitation_worth(self, node_id: str, world: Any) -> float:
		return 0.0

	def credit_earning(self, world: Any) -> float:
		return max(0.0, self.record.last_margin)

	# ---- concerns ---------------------------------------------------------
	def begin_concern(self, node_id: str, world: Any) -> str:
		if node_id not in world.nodes:
			raise CommandRejected("no such node")
		if not self.knows(node_id, world):
			raise CommandRejected("not known")
		if node_id in self.concerns:
			raise CommandRejected("already open")
		self.business.open_plant(node_id, world.year)
		return "opened"

	def end_concern(self, node_id: str, world: Any) -> str:
		if node_id not in self.concerns:
			raise CommandRejected("not open")
		self.business.close_plant(node_id)
		return "closed"

	def operate(self, world: Any) -> None:
		for node_id in sorted(self.concerns):
			rivals = self.rivals_of(node_id, self.actor_id) if self.rivals_of else 0.0
			self.business.note_margin(node_id, business_books.operate(self.business, self, node_id, world, rivals))
		self.record.last_margin = sum(plant.margin for plant in self.business.plants if plant.margin is not None)

	def proven_concerns(self, world: Any) -> List[str]:
		"""Concerns it runs at a profit where others could see them, for competitors to enter after."""
		proven = []
		for node_id in sorted(self.concerns):
			if (self.margin_of(node_id) or 0.0) <= 0.0:
				continue
			if world.year - self.opened_year_of(node_id, world.year) < world.proof_years(node_id):
				continue
			if world.is_public(node_id) or world.exposure(node_id, self.location()) >= PLAYER_VISIBLE_EXPOSURE:
				proven.append(node_id)
		return proven

	# ---- money ------------------------------------------------------------
	def send_money(self, payee_id: Any, amount: float) -> str:
		payee = self.find_actor(payee_id) if self.find_actor is not None and isinstance(payee_id, str) else None
		if payee is None or payee is self:
			raise CommandRejected("no such payee")
		if not math.isfinite(amount) or amount <= 0:
			raise CommandRejected("amount must be positive")
		if amount > max(0.0, self.money):
			raise CommandRejected("not enough money")
		ledger.transfer(self, payee, amount, "transfer")
		return "paid %.2f to %s" % (amount, payee_id)

	# ---- the AI's own decisions -------------------------------------------
	def expected_margin(self, node_id: str, world: Any) -> float:
		"""Yearly margin a new operator expects from a concern at full ramp."""
		return research_choice.expected_concern_margin(self, node_id, world)

	def research_worth(self, node_id: str, world: Any) -> float:
		return research_choice.concern_worth(self, node_id, world)

	def decide(self, world: Any) -> None:
		"""An AI player: shut what it expects to lose on, open what it knows pays, research what is worth it."""
		for node_id in sorted(self.concerns):
			if (self.margin_of(node_id) or 0.0) < 0 and self.expected_margin(node_id, world) <= 0:
				self.business.close_plant(node_id)
		for node_id in sorted(self.knowledge - self.concerns):
			if node_id in world.nodes and self.expected_margin(node_id, world) > 0:
				self.business.open_plant(node_id, world.year)
		research_choice.decide(self, world)

	def act(self, world: Any) -> None:
		self.pay_interest(world)
		run_orders(self, world)
		if self.record.controller == "ai":
			self.decide(world)
		self.workforce.clear()
		self.work_on_research(world)
		self.operate(world)


register_actor_kind("player", Player)
