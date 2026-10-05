"""The founder's household as a party to an exchange.

An exchange handles an actor with `actor_id`, `money`, `concerns`, `knows`, `learn`, `credit`, `debit`,
`opened_year_of`, `capacity_of` and a `record` (stores, offers, opened year, margins). The household keeps
that state in the simulation state, so this adapter maps the names onto it: concerns are the household's
operating set, opened years its own dictionary, and the purse its capital.
"""
from typing import Any, Dict, Optional

from .records import ActorRecord

FOUNDER_ACTOR_ID = "founder"


class HouseholdParty:
	"""Gives a `Household` the surface an exchange needs; holds no state of its own beyond a transient record."""

	kind = "household"
	actor_id = FOUNDER_ACTOR_ID

	def __init__(self, household: Any, margins: Optional[Dict[str, float]] = None) -> None:
		self.household = household
		projects = household._state.projects
		if projects.opened_year is None:
			projects.opened_year = {}
		# the opened-year dictionary is the household's own, so opening and closing write through
		self.record = ActorRecord(kind="household", opened_year=projects.opened_year, margins=dict(margins or {}))

	@property
	def money(self) -> float:
		return self.household.money

	@money.setter
	def money(self, value: float) -> None:
		self.household.money = value

	@property
	def concerns(self) -> Any:
		return self.household.operating

	@property
	def knowledge(self) -> Any:
		return self.household.done

	def identity(self) -> str:
		return self.actor_id

	def knows(self, node_id: str, world: Any) -> bool:
		return self.household.knows(node_id, world)

	def learn(self, chain: Any, world: Any) -> None:
		self.household.done.update(chain)

	def credit(self, amount: float, purpose: Any) -> None:
		self.household.credit(amount, purpose)

	def debit(self, amount: float, purpose: Any) -> None:
		self.household.debit(amount, purpose)

	def opened_year_of(self, node_id: str, default: int) -> int:
		return self.household.opened_year_of(node_id, default)

	def capacity_of(self, node_id: str) -> float:
		return 1.0
