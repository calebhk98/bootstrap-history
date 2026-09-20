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
`ProjectsState`, `EconomyState`, `GovernanceState`, `FounderState`,
`ScenarioState`, `PopulationState`). There is NO duplicate storage: every
persistent read and write delegates directly to the underlying typed state.
"""
import collections
from collections import defaultdict
from typing import (Any, Callable, DefaultDict, Dict, Iterable, List,
					 Optional, Set, Tuple, TypedDict)

from ..economy import _InvalidatingSet, _InvalidatingDict
from sim.engine.state import (
	ActiveProjectState,
	SimulationState,
	HouseholdState,
	ProjectsState,
	EconomyState,
	GovernanceState,
	FounderState,
	ScenarioState,
	PopulationState,
)


class MineWorking(TypedDict):
	"""One entry of `self.mines`, below - a single owned mining operation.
	Fixed at exactly these five fields: the only place any of these dicts is
	built is `commission_mines()` (economy_mining.py), which always writes
	all five, and every read site across economy_mining.py reads only
	`material`, `capacity` and `intensity_yrs` (`opened_year` and
	`capex_paid` exist for save/display, not for the mining arithmetic
	itself) - none of them, in that file or anywhere else, adds a sixth
	key. Contrast `ActiveProjectState` below, which stays a plain mapping
	because ITS dicts genuinely do grow new keys at runtime."""
	material: str
	capacity: float
	opened_year: int
	capex_paid: float
	intensity_yrs: float


_SUBSYSTEM_MAP: Dict[str, str] = {
	# HouseholdState
	"capital": "household",
	"total_spend": "household",
	"bounties_paid": "household",
	"wages_paid": "household",
	"wages_prepaid": "household",
	"wages_earned": "household",
	"interest_paid": "household",
	"reputation": "household",
	"scandal": "household",
	"scandal_last_year": "household",
	"eminence": "household",
	"familiarity": "household",
	"protection": "household",
	"bribes_ytd": "household",
	"slaves": "household",
	"freedmen": "household",
	"manumitted_total": "household",
	"atrocity": "household",
	"bondage_years_left": "household",
	"bondage_debt": "household",
	"credit_frozen_until": "household",
	"insolvent_years": "household",
	"last_withdrawal": "household",
	"last_settlement": "household",
	"spend_last_year": "household",
	"scholars": "household",
	"artisans": "household",
	"directors_extra": "household",
	"employees": "household",
	"trades_created": "household",
	"trades_endemic": "household",
	"trade_introduced_year": "household",
	"contract_hours": "household",
	"commissioned": "household",
	"teaching_hours_this_year": "household",
	"hour_allocations": "household",
	"work_trade": "household",
	"last_taught": "household",
	"training": "household",
	"wage_hours_this_year": "household",
	"log": "household",
	"granted_staff": "household",
	"hours_this_year": "household",
	"trade_schools": "household",
	"worker_housing_places": "household",
	"_said_deputies": "household",
	"_said_near_limit": "household",
	"_said_autoopen": "household",
	"_said_eminence": "household",
	"_said_requisition": "household",
	"_said_notice_approach": "household",
	"last_military_demand": "household",
	"_said_confiscation_band": "household",
	"_said_scandal": "household",

	# ProjectsState
	"active": "projects",
	"done": "projects",
	"done_year": "projects",
	"operating": "projects",
	"failed_attempts": "projects",
	"mothballed": "projects",
	"bountied": "projects",
	"granted": "projects",
	"opened_year": "projects",
	"paid_towards": "projects",
	"forgotten": "projects",
	"trade_hours_used": "projects",
	"revealed": "projects",
	"stalled": "projects",
	"shut_for_staff": "projects",

	# EconomyState
	"mines": "economy",
	"mine_pending": "economy",
	"mine_ready": "economy",
	"mine_cost_paid": "economy",
	"mine_tranches": "economy",
	"shortages": "economy",
	"throttle": "economy",
	"binding": "economy",
	"forest_ha": "economy",
	"nitre_bed_m2": "economy",
	"market_pressure": "economy",
	"output_factor": "economy",
	"economy": "economy",
	"money_real": "economy",
	"_material_stock_ledger": "economy",
	"farm_hectares": "economy",
	"farm_stock_kg": "economy",
	"_dashboard_history": "economy",

	# GovernanceState
	"inst_units": "governance",
	"gov": "governance",

	# FounderState
	"founder_alive": "founder",
	"life_left": "founder",
	"dead_reason": "founder",
	"director_hours_spent_founder": "founder",
	"living_cost_paid": "founder",
	"policy": "founder",
	"last_patron_death": "founder",
	"_founder_death_aged": "founder",
	"_founder_death_year": "founder",

	# ScenarioState
	"year": "scenario",
	"goal_year": "scenario",
	"_said_debasement": "scenario",
	"_said_output": "scenario",
	"_said_scandal": "scenario",
	"_said_parallelism": "scenario",
	"_said_command_index": "scenario",

	# PopulationState
	"pop_children": "population",
	"pop_working_age": "population",
	"pop_elderly": "population",
	"_food_pop_bonus_applied": "population",
}

_VERSION_MAP: Dict[str, str] = {
	"_operating_ver": "projects",
	"_done_ver": "projects",
	"_active_ver": "projects",
	"_workforce_ver": "household",
	"_inst_units_ver": "governance",
}

_LAZY_FIELDS: Set[str] = {
	"wages_earned",
	"interest_paid",
	"insolvent_years",
	"last_withdrawal",
	"spend_last_year",
	"granted_staff",
	"hours_this_year",
	"trade_schools",
	"worker_housing_places",
	"_said_deputies",
	"_said_near_limit",
	"_said_autoopen",
	"done_year",
	"shut_for_staff",
	"mine_tranches",
	"_material_stock_ledger",
	"farm_hectares",
	"_dashboard_history",
	"inst_units",
	"wage_hours_this_year",
	"_said_scandal",
	"_said_parallelism",
}


class Household:
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
		workforce_changed: Optional[Callable[[], None]] = None,
		state: Optional[SimulationState] = None,
		sim: Optional[Any] = None,
	) -> None:
		self._sim = sim
		if state is not None:
			self._state = state
			self._state.household.capital = float(starting_capital)
		elif sim is not None and hasattr(sim, "state") and sim.state is not None:
			self._state = sim.state
			self._state.household.capital = float(starting_capital)
		else:
			self._state = SimulationState(
				household=HouseholdState(capital=float(starting_capital)),
				projects=ProjectsState(),
				economy=EconomyState(),
				governance=GovernanceState(),
				founder=FounderState(),
				scenario=ScenarioState(),
				population=PopulationState(),
			)

		# Wrap mutation-aware collections with callbacks if provided
		if operating_changed is not None:
			self._state.projects.operating = _InvalidatingSet(
				self._state.projects.operating or set(),
				on_change=operating_changed
			)
		if active_changed is not None:
			self._state.projects.active = _InvalidatingDict(
				{k: ActiveProjectState.from_dict(v if isinstance(v, dict) else v.to_canon_dict(), _on_change=active_changed)
				 for k, v in (self._state.projects.active or {}).items()},
				on_change=active_changed
			)
		if workforce_changed is not None:
			self._state.household.employees = _InvalidatingDict(
				self._state.household.employees or {},
				on_change=workforce_changed
			)

		# Version counters attached to owning subsystems
		if getattr(self._state.projects, "_operating_ver", None) is None:
			self._state.projects._operating_ver = 0  # type: ignore[attr-defined]
		if getattr(self._state.projects, "_done_ver", None) is None:
			self._state.projects._done_ver = 0  # type: ignore[attr-defined]
		if getattr(self._state.projects, "_active_ver", None) is None:
			self._state.projects._active_ver = 0  # type: ignore[attr-defined]
		if getattr(self._state.household, "_workforce_ver", None) is None:
			self._state.household._workforce_ver = 0  # type: ignore[attr-defined]
		if self._state.governance is not None and getattr(self._state.governance, "_inst_units_ver", None) is None:
			self._state.governance._inst_units_ver = 0  # type: ignore[attr-defined]

		# Transient caches and runtime-only trackers
		self.contract_projects: Set[str] = set()
		self._done_seq: Optional[List[str]] = None
		self._cap_factor: Optional[float] = None
		self._staff_scale: float = 1.0
		self._spend_this_year: float = 0.0
		self._revenue_cache_key: Any = None
		self._revenue_cache_val: Any = None
		self._annual_mat_demand_cache: Any = None
		self._rev_up_candidates_cache: Any = None
		self._practice_cache: Any = None
		self._goods_cat_state_cache: Any = None
		self._goods_category_ratios_cache: Any = None
		self._income_factor_cache: Any = None
		self._goods_mkt_op_factor_cache: Any = None
		self._material_demand_cache: Any = None
		self._demand_by_tag_cache: Any = None
		self._freight_distance_km_cache: Any = None
		self._demand_by_emp_key_cache: Any = None
		self._stock_throttle_sig: Any = None
		self._last_buy_refusal: Any = None
		self._said_stack_caution: Any = None

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
	def done(self) -> Any:
		return self._state.projects.done

	@done.setter
	def done(self, value: Any) -> None:
		self._state.projects.done = value

	@property
	def operating(self) -> Any:
		return self._state.projects.operating

	@operating.setter
	def operating(self, value: Any) -> None:
		self._state.projects.operating = value

	@property
	def employees(self) -> Any:
		return self._state.household.employees

	@employees.setter
	def employees(self, value: Any) -> None:
		self._state.household.employees = value

	@property
	def mines(self) -> Any:
		if self._state.economy is None:
			return []
		return self._state.economy.mines

	@mines.setter
	def mines(self, value: Any) -> None:
		if self._state.economy is not None:
			self._state.economy.mines = value

	@property
	def shortages(self) -> Any:
		if self._state.economy is None:
			return collections.Counter()
		return self._state.economy.shortages

	@shortages.setter
	def shortages(self, value: Any) -> None:
		if self._state.economy is not None:
			self._state.economy.shortages = value

	@property
	def failed_attempts(self) -> Any:
		return self._state.projects.failed_attempts

	@failed_attempts.setter
	def failed_attempts(self, value: Any) -> None:
		self._state.projects.failed_attempts = value

	@property
	def revealed(self) -> Set[str]:
		return self._state.projects.revealed

	@revealed.setter
	def revealed(self, value: Iterable[str]) -> None:
		cur = self._state.projects.revealed
		self._state.projects.revealed = (set(value) if cur is None
										 else set(cur) | set(value))

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
	def _workforce_ver(self) -> int:
		return int(getattr(self._state.household, "_workforce_ver", 0))

	@_workforce_ver.setter
	def _workforce_ver(self, value: int) -> None:
		setattr(self._state.household, "_workforce_ver", int(value))

	@property
	def _inst_units_ver(self) -> int:
		if self._state.governance is None:
			return 0
		return int(getattr(self._state.governance, "_inst_units_ver", 0))

	@_inst_units_ver.setter
	def _inst_units_ver(self, value: int) -> None:
		if self._state.governance is not None:
			setattr(self._state.governance, "_inst_units_ver", int(value))

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
		if (name in ("_state", "_sim", "contract_projects")
				or name.startswith("_cap_factor")
				or name.startswith("_staff_scale")
				or name.startswith("_spend_this_year")
				or name.endswith("_cache")
				or name.startswith("_revenue_cache")
				or name.startswith("_stock_throttle")
				or name == "_last_buy_refusal"
				or name == "_said_stack_caution"
				or name == "_done_seq"):
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
