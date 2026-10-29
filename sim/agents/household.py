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
`ProjectsState`, `EconomyState`, `FounderState`). There is NO duplicate storage: every
persistent read and write delegates directly to the underlying typed state.
"""
from collections import defaultdict
from typing import (Any, Callable, DefaultDict, Dict, Iterable, List,
					 Optional, Set, Tuple)

from sim.invalidating import ActiveProjectState, _InvalidatingSet, _InvalidatingDict
from .base import Actor
from .business_founder_review import FounderReview
from .household_borrowing import FounderBorrowing
from .policy import IdlePolicy


_SUBSYSTEM_MAP: Dict[str, str] = {
	# HouseholdState
	"capital": "household",
	"total_spend": "household",
	"bounties_paid": "household",
	"cash_flow": "household",
	"cash_mark": "household",
	"cash_periods": "household",
	"spend_last_year": "household",

	# ProjectsState
	"active": "projects",
	"operating": "projects",
	"failed_attempts": "projects",
	"mothballed": "projects",
	"bountied": "projects",
	"opened_year": "projects",
	"paid_towards": "projects",
	"stalled": "projects",
	"closures": "projects",

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

_VERSION_MAP: Dict[str, str] = {
	"_operating_ver": "projects",
	"_done_ver": "projects",
	"_active_ver": "projects",
	"_inst_units_ver": "household",
}

_LAZY_FIELDS: Set[str] = {
	"spend_last_year",
	"_dashboard_history",
}


class Household(FounderReview, FounderBorrowing, Actor):
	"""The founder's household: money, staff, knowledge, plant and standing.

	In the live state architecture, Household delegates all persistent state
	reads and writes to the live SimulationState subsystem objects. There is
	only one authoritative copy of persistent state in memory.
	"""

	def __init__(
		self,
		starting_capital: float = 0.0,
		operating_changed: Optional[Callable[[], None]] = None,
		active_changed: Optional[Callable[[], None]] = None,
		state: Optional[Any] = None,
		port: Optional[Any] = None,
		techniques_held: Optional[Callable[[], Any]] = None,
	) -> None:
		# The founder's choices arrive as commands, so the household idles.
		Actor.__init__(self, IdlePolicy())
		self._port = port
		self._techniques_held = techniques_held
		if state is not None:
			self._state = state
			self._state.household.capital = float(starting_capital)
		else:
			self._state = port.fresh_state(starting_capital)

		self._state.household.cash_mark = float(starting_capital)

		# Wrap mutation-aware collections with callbacks if provided
		if operating_changed is not None:
			self._state.projects.business.watch = operating_changed
		if active_changed is not None:
			self._state.projects.active = _InvalidatingDict(
				{k: ActiveProjectState.from_dict(v if isinstance(v, dict) else v.to_canon_dict(), _on_change=active_changed)
				 for k, v in (self._state.projects.active or {}).items()},
				on_change=active_changed
			)
		# Version counters attached to owning subsystems
		self.start_version_counters(self._state)

		# Transient caches and runtime-only trackers
		self.contract_projects: Set[str] = set()
		self._spend_this_year: float = 0.0
		self._goods_cat_state_cache: Any = None
		self._goods_category_ratios_cache: Any = None
		self._income_factor_cache: Any = None
		self._goods_mkt_op_factor_cache: Any = None
		self._said_stack_caution: Any = None

	kind = "household"

	@property
	def money(self) -> float:
		return self.capital

	@money.setter
	def money(self, value: float) -> None:
		self.capital = value

	@property
	def purses(self) -> Any:  # type: ignore[override]
		return self._state.household.ledger_purses

	@property
	def account_id(self) -> str:
		return self._state.household.account

	def note_income(self, purpose: Any, amount: float) -> None:
		self._state.household.note_income(purpose, amount)

	def note_outlay(self, purpose: Any, amount: float) -> None:
		self._state.household.note_outlay(purpose, amount)

	def credit(self, amount: float, purpose: Any) -> None:
		self._state.household.credit(amount, purpose)

	def debit(self, amount: float, purpose: Any) -> None:
		self._state.household.debit(amount, purpose)

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
	def capital(self) -> float:
		return self._state.household.capital

	@capital.setter
	def capital(self, value: float) -> None:
		self._state.household.capital = float(value)

	@property
	def active(self) -> Any:
		return self._state.projects.active

	@active.setter
	def active(self, value: Any) -> None:
		self._state.projects.active = value

	@property
	def operating(self) -> Any:
		return self._state.projects.operating

	@operating.setter
	def operating(self, value: Any) -> None:
		self._state.projects.operating = value

	@property
	def failed_attempts(self) -> Any:
		return self._state.projects.failed_attempts

	@failed_attempts.setter
	def failed_attempts(self, value: Any) -> None:
		self._state.projects.failed_attempts = value

	@property
	def _operating_ver(self) -> int:
		return int(getattr(self._state.projects, "_operating_ver", 0))

	@_operating_ver.setter
	def _operating_ver(self, value: int) -> None:
		setattr(self._state.projects, "_operating_ver", int(value))

	@property
	def _done_ver(self) -> int:
		return int(getattr(self._state.projects, "_done_ver", 0))

	@_done_ver.setter
	def _done_ver(self, value: int) -> None:
		setattr(self._state.projects, "_done_ver", int(value))

	@property
	def _active_ver(self) -> int:
		return int(getattr(self._state.projects, "_active_ver", 0))

	@_active_ver.setter
	def _active_ver(self, value: int) -> None:
		setattr(self._state.projects, "_active_ver", int(value))

	@property
	def _inst_units_ver(self) -> int:
		return int(getattr(self._state.household, "_inst_units_ver", 0))

	@_inst_units_ver.setter
	def _inst_units_ver(self, value: int) -> None:
		setattr(self._state.household, "_inst_units_ver", int(value))

	@property
	def operating_version(self) -> int:
		return self._operating_ver

	@property
	def done_version(self) -> int:
		return self._done_ver

	@property
	def active_version(self) -> int:
		return self._active_ver

	@property
	def institution_units_version(self) -> int:
		return self._inst_units_ver

	def bump_done_version(self) -> None:
		self._done_ver = self._done_ver + 1

	def bump_operating_version(self) -> None:
		self._operating_ver = self._operating_ver + 1

	def bump_active_version(self) -> None:
		self._active_ver = self._active_ver + 1

	def bump_institution_units_version(self) -> None:
		self._inst_units_ver = self._inst_units_ver + 1

	def start_version_counters(self, state: Any) -> None:
		"""Give each version counter on `state`'s owning subsystems a zero where it has none."""
		if getattr(state.projects, "_operating_ver", None) is None:
			state.projects._operating_ver = 0  # type: ignore[attr-defined]
		if getattr(state.projects, "_done_ver", None) is None:
			state.projects._done_ver = 0  # type: ignore[attr-defined]
		if getattr(state.projects, "_active_ver", None) is None:
			state.projects._active_ver = 0  # type: ignore[attr-defined]
		if getattr(state.household, "_inst_units_ver", None) is None:
			state.household._inst_units_ver = 0  # type: ignore[attr-defined]

	def opened_year_of(self, node_id: str, default: int) -> int:
		return self._state.projects.business.opened_year_of(node_id, default)

	def __getattr__(self, name: str) -> Any:
		if name.startswith("_state"):
			raise AttributeError(name)
		state = self.__dict__.get("_state")
		if state is None:
			raise AttributeError(name)
		# Check version counters
		ver_owner = _VERSION_MAP.get(name)
		if ver_owner is not None:
			owner_obj = getattr(state, ver_owner, None)
			if owner_obj is not None:
				return getattr(owner_obj, name, 0)
			return 0
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
				or name.startswith("_spend_this_year")
				or name.endswith("_cache")
				or name == "_said_stack_caution"):
			super().__setattr__(name, value)
			return

		state = self.__dict__.get("_state")
		if state is not None:
			ver_owner = _VERSION_MAP.get(name)
			if ver_owner is not None:
				owner_obj = getattr(state, ver_owner, None)
				if owner_obj is not None:
					setattr(owner_obj, name, value)
					return
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
