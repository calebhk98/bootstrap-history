"""`Household`: the founder and family as an economic actor.

Money, staff, knowledge, standing and every cache keyed off any of them
live here, not on the `Sim` god object, so something other than the
founder's own household - a government, a rival household, a firm - can
someday own a purse and a stock of knowledge of its own without needing a
second `Sim`. See `docs/architecture/HOUSEHOLD_EXTRACTION.md` for the
design and `docs/architecture/SIM_STATE_INVENTORY.md` for the measured
field-by-field classification this class is built from.

In the live state architecture, `Household` is a façade backed by the
authoritative `SimulationState` and its subsystem owners (`HouseholdState`,
`EconomyState`, `FounderState`). There is NO duplicate storage: every
persistent read and write delegates directly to the underlying typed state.
"""
from collections import defaultdict
from typing import (Any, Callable, DefaultDict, Dict, Iterable, List,
					 Optional, Set, Tuple)

from .base import Actor
from .business_founder_review import FounderReview
from .household_borrowing import FounderBorrowing
from .policy import IdlePolicy


_SUBSYSTEM_MAP: Dict[str, str] = {
	# EconomyState
	"_dashboard_history": "holdings",

	# FounderState
	"policy": "founder",
	"_founder_death_aged": "founder",
	"_founder_death_year": "founder",

	# SeatProgressState
	"_said_parallelism": "seat_progress",
	"_said_command_index": "seat_progress",
	"_said_explanations": "seat_progress",
}

_LAZY_FIELDS: Set[str] = {
	"_dashboard_history",
}


class Household(FounderReview, FounderBorrowing, Actor):
	"""The founder's household: money, staff, knowledge, plant and standing.

	In the live state architecture, Household delegates all persistent state
	reads and writes to the live SimulationState subsystem objects. There is
	only one authoritative copy of persistent state in memory.
	"""

	def __init__(self, state: Any, port: Any, techniques_held: Callable[[], Any]) -> None:
		"""`port` answers for the seat's money: the ledger's views and commands (see `SeatMoneyPort`)."""
		# The founder's choices arrive as commands, so the household idles.
		Actor.__init__(self, IdlePolicy())
		self._port = port
		self._techniques_held = techniques_held
		self._state = state

		# Transient caches and runtime-only trackers
		self.contract_projects: Set[str] = set()
		self._goods_cat_state_cache: Any = None
		self._goods_category_ratios_cache: Any = None
		self._income_factor_cache: Any = None
		self._goods_mkt_op_factor_cache: Any = None
		self._said_stack_caution: Any = None

	kind = "household"

	@property
	def money(self) -> float:
		return self._port.balance()

	@money.setter
	def money(self, value: float) -> None:
		self._port.set_balance(value)

	@property
	def purses(self) -> Any:  # type: ignore[override]
		return self._port.purses()

	@property
	def account_id(self) -> str:
		return self._state.acting_seat

	def note_income(self, purpose: Any, amount: float) -> None:
		self._port.note_cash(1.0, amount, purpose)

	def note_outlay(self, purpose: Any, amount: float) -> None:
		self._port.note_cash(-1.0, amount, purpose)

	def credit(self, amount: float, purpose: Any) -> None:
		self._port.credit(amount, purpose)

	def debit(self, amount: float, purpose: Any) -> None:
		self._port.debit(amount, purpose)

	def _polity(self) -> Any:
		"""The acting seat's polity slot: the founder's answers to the state's demands live in it (a debt: the founder's
		household is not yet an actor the polity module serves through its views)."""
		return self._state.seats[self._state.acting_seat].modules["polity"]

	def service_worth(self) -> float:
		return float(self._polity().service_offer)

	def concealed_wealth(self) -> float:
		return float(self._polity().concealed)

	def defiance(self) -> float:
		return float(self._polity().defiance)

	def set_concealed_wealth(self, amount: float) -> None:
		self._polity().concealed = max(0.0, amount)

	def set_defiance(self, level: float) -> None:
		self._polity().defiance = level

	def _workforce(self) -> Any:
		"""The acting seat's workforce slot: its payroll is the household actor's `workforce` (a debt: the household is not yet an
		actor the workforce module serves through its views)."""
		return self._state.seats[self._state.acting_seat].modules["workforce"]

	@property
	def workforce(self) -> Any:
		return self._workforce().employees

	@property
	def knowledge(self) -> Any:
		"""The nodes the acting seat holds, as the knowledge module answers them (the engine hands this household the question)."""
		return self._techniques_held()

	@property
	def concerns(self) -> Any:
		return self.operating

	@property
	def works(self) -> Any:
		return self.active

	def imitation_worth(self, node_id: str, world: Any) -> float:
		return 0.0

	@property
	def active(self) -> Any:
		"""The projects in hand of the acting seat: the projects module's seat state (a debt, like the staff)."""
		return self._state.seats[self._state.acting_seat].modules["projects"].active

	@active.setter
	def active(self, value: Any) -> None:
		self._state.seats[self._state.acting_seat].modules["projects"].active = value

	def _business(self) -> Any:
		"""The acting seat's own business: the ventures module's seat state (a debt, like the staff and the projects in hand)."""
		return self._state.seats[self._state.acting_seat].modules["ventures"].business

	@property
	def operating(self) -> Any:
		return self._business().operating()

	def opened_year_of(self, node_id: str, default: int) -> int:
		return self._business().opened_year_of(node_id, default)

	def __getattr__(self, name: str) -> Any:
		if name.startswith("_state"):
			raise AttributeError(name)
		state = self.__dict__.get("_state")
		if state is None:
			raise AttributeError(name)
		# Check subsystem state
		subsystem_name = _SUBSYSTEM_MAP.get(name)
		if subsystem_name is not None:
			subsystem = getattr(state, subsystem_name, None)
			if subsystem is not None and hasattr(subsystem, name):
				val = getattr(subsystem, name)
				if val is None and name in _LAZY_FIELDS:
					raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
				return val
		raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

	def __setattr__(self, name: str, value: Any) -> None:
		if (name in ("_state", "_port", "_techniques_held", "contract_projects")
				or name.endswith("_cache")
				or name == "_said_stack_caution"):
			super().__setattr__(name, value)
			return

		state = self.__dict__.get("_state")
		if state is not None:
			subsystem_name = _SUBSYSTEM_MAP.get(name)
			if subsystem_name is not None:
				subsystem = getattr(state, subsystem_name, None)
				if subsystem is not None:
					setattr(subsystem, name, value)
					return
		super().__setattr__(name, value)

	def __delattr__(self, name: str) -> None:
		state = self.__dict__.get("_state")
		if state is not None:
			subsystem_name = _SUBSYSTEM_MAP.get(name)
			if subsystem_name is not None:
				subsystem = getattr(state, subsystem_name, None)
				if subsystem is not None and hasattr(subsystem, name):
					setattr(subsystem, name, None)
					return
		super().__delattr__(name)
