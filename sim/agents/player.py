"""`Player`: a second (third, ...) player in the same game, human, LLM or AI.

It has its own purse, research tree, staff, concerns and works. Like the founder it comes from the
future, so it may research any node whose prerequisites it knows, not only what someone showed it.
A human or LLM player acts only through queued orders (`player_commands.py`) and runs what it owns;
an AI player also decides for itself.
"""
import math
from typing import Any, Callable, Dict, List, Optional

from . import concern_ops, imitation, ledger
from .base import RecordedActor
from .player_commands import CommandRejected, run_orders
from .policy import Decision, Option
from .registry import register_actor_kind
from .tuning import ATTENTION_SPAN, HIRING_PREMIUM, VALUE_HORIZON_YEARS
from .tuning_player import PLAYER_VISIBLE_EXPOSURE


class Player(RecordedActor):
	kind = "player"

	# Set by the registry: how many other operators share a concern's market.
	rivals_of: Optional[Callable[[str, str], float]] = None
	# Set by the registry: the actor with an id, or None; how a payment finds its payee.
	find_actor: Optional[Callable[[str], Any]] = None

	def imitation_worth(self, node_id: str, world: Any) -> float:
		return 0.0

	def credit_earning(self, world: Any) -> float:
		return max(0.0, self.record.last_margin)

	# ---- research ---------------------------------------------------------
	def missing_prerequisites(self, node_id: str, world: Any) -> List[str]:
		return [pre for pre in world.nodes[node_id].get("pre") or () if not self.knows(pre, world)]

	def research_plan(self, node_id: str, world: Any) -> Dict[str, Any]:
		"""Hours, money and calendar for pioneering one node at full effort."""
		node = world.nodes[node_id]
		hours = dict(node.get("lab") or {})
		base_labour = sum(amount * world.labour_market.quote(trade, 0.0, self) for trade, amount in hours.items())
		premium = sum(amount * world.labour_market.quote(trade, 0.0, self) * HIRING_PREMIUM
					  for trade, amount in hours.items() if self.workforce.get(trade, 0.0) <= 0)
		other_money = max(0.0, world.copy_cost(node_id) - base_labour)
		return {"hours": hours, "money": other_money + premium, "labour_cost": base_labour,
				"total": other_money + premium + base_labour,
				"years": max(1, int(math.ceil(float(node.get("yrs") or 0.0))))}

	def research_chance(self, node_id: str, world: Any) -> float:
		return 1.0 - min(1.0, world.copy_risk(node_id))

	def start_research(self, node_id: str, world: Any) -> str:
		"""Begin researching a node; refuses with the reason."""
		if node_id not in world.nodes:
			raise CommandRejected("no such node")
		if self.knows(node_id, world):
			raise CommandRejected("already known")
		if node_id in self.works:
			raise CommandRejected("already being researched")
		missing = self.missing_prerequisites(node_id, world)
		if missing:
			raise CommandRejected("prerequisites unknown: " + ", ".join(sorted(missing)))
		plan = self.research_plan(node_id, world)
		if plan["total"] > self.copy_budget(world):
			raise CommandRejected("cannot afford the research")
		self.works[node_id] = imitation.start_work(node_id, [node_id], plan, world.year)
		return "research begun, %d years" % plan["years"]

	def work_on_research(self, world: Any) -> List[str]:
		"""Advance every research a year; returns the nodes learned."""
		self.workforce.clear()
		learned = []
		for node_id in sorted(self.works):
			work = self.works[node_id]
			if not imitation.work_year(self, node_id, work, world):
				continue
			del self.works[node_id]
			roll = world.rng_for(world.year, self.kind, node_id, self.identity())
			if roll.random() < self.research_chance(node_id, world):
				self.learn([node_id], world)
				learned.append(node_id)
			else:
				self.record_failure(node_id)
		return learned

	# ---- concerns ---------------------------------------------------------
	def begin_concern(self, node_id: str, world: Any) -> str:
		if node_id not in world.nodes:
			raise CommandRejected("no such node")
		if not self.knows(node_id, world):
			raise CommandRejected("not known")
		if node_id in self.concerns:
			raise CommandRejected("already open")
		concern_ops.open_concern(self, node_id, world)
		return "opened"

	def end_concern(self, node_id: str, world: Any) -> str:
		if node_id not in self.concerns:
			raise CommandRejected("not open")
		concern_ops.close_concern(self, node_id)
		return "closed"

	def operate(self, world: Any) -> None:
		for node_id in sorted(self.concerns):
			rivals = self.rivals_of(node_id, self.actor_id) if self.rivals_of else 0.0
			self.record.margins[node_id] = concern_ops.operate_concern(self, node_id, world, rivals)
		self.record.last_margin = sum(self.record.margins.values())

	def proven_concerns(self, world: Any) -> List[str]:
		"""Concerns it runs at a profit where others could see them, for competitors to enter after."""
		proven = []
		for node_id in sorted(self.concerns):
			if self.record.margins.get(node_id, 0.0) <= 0.0:
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
		rivals = self.rivals_of(node_id, self.actor_id) if self.rivals_of else 0.0
		return world.entry_gross(node_id, rivals, 1.0) - world.upkeep(node_id) - world.concern_wage_bill(node_id)

	def research_options(self, world: Any) -> List[Option]:
		candidates = []
		for node_id in sorted(world.nodes):
			if self.knows(node_id, world) or node_id in self.works or self.missing_prerequisites(node_id, world):
				continue
			margin = self.expected_margin(node_id, world)
			if margin > 0:
				candidates.append((margin * VALUE_HORIZON_YEARS, node_id))
		candidates.sort(key=lambda item: (-item[0], item[1]))
		return [Option(subject=node_id, worth=worth, cost=self.research_plan(node_id, world)["total"],
					   chance=self.research_chance(node_id, world))
				for worth, node_id in candidates[:ATTENTION_SPAN]]

	def decide(self, world: Any) -> None:
		"""An AI player: shut what it expects to lose on, open what it knows pays, research what is worth it."""
		for node_id in sorted(self.concerns):
			if self.record.margins.get(node_id, 0.0) < 0 and self.expected_margin(node_id, world) <= 0:
				concern_ops.close_concern(self, node_id)
		for node_id in sorted(self.knowledge - self.concerns):
			if node_id in world.nodes and self.expected_margin(node_id, world) > 0:
				concern_ops.open_concern(self, node_id, world)
		options = self.research_options(world)
		for option in self.decision_policy.choose(self, Decision("research", options, self.copy_budget(world))):
			try:
				self.start_research(option.subject, world)
			except CommandRejected:
				continue

	def act(self, world: Any) -> None:
		self.pay_interest(world)
		run_orders(self, world)
		if self.record.controller == "ai":
			self.decide(world)
		self.work_on_research(world)
		self.operate(world)


register_actor_kind("player", Player)
