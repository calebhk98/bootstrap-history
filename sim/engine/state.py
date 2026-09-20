"""Authoritative simulation state definitions and explicit subsystem state owners.

Every persistent mutable field in the simulation belongs to one authoritative
state owner defined in this module. Transient caches, version counters, derived
values, and invalidation plumbing remain non-persistent implementation details.
"""
import collections
import dataclasses
from dataclasses import dataclass, field
from typing import (
	Any, Callable, Counter, DefaultDict, Dict, Iterable, List,
	Optional, Set, Tuple, Union, get_args, get_origin, get_type_hints,
)

from sim.engine.economy import _InvalidatingDict


@dataclass(init=False)
class ActiveProjectState(_InvalidatingDict):
	"""Explicit schema for an active technology, project, or venture in progress.

	Owns progress towards completion, founder hours, financial commitment,
	and trade labour allocation.
	"""
	ph_left: float
	yrs: float = 0.0
	spent: float = 0.0
	cost_left: float = 0.0
	lab_left: Optional[Dict[str, float]] = None

	# Per-step allocation and progress accounting
	hours_offered_this_year: Optional[float] = None
	hours_directed_this_year: Optional[float] = None
	hours_effective_this_year: Optional[float] = None
	pool_total_this_year: Optional[float] = None
	pool_active_count_this_year: Optional[int] = None
	pool_rank_this_year: Optional[int] = None
	pool_remaining_before_this_year: Optional[float] = None

	# Stall, blockage, and funding status
	stalled_years: Optional[int] = None
	blocked_on_trades: Optional[List[str]] = None
	underfunded_this_year: Optional[bool] = None
	why_underfunded: Optional[str] = None
	short_of_trade: Optional[List[str]] = None
	waiting_on_money: Optional[bool] = None

	# Operational flags
	paused: Optional[bool] = None
	mothballed: Optional[bool] = None

	# Invalidation hook (transient, excluded from comparison and serialization)
	_on_change: Optional[Callable[[], None]] = field(default=None, repr=False, compare=False)

	def __init__(
		self,
		ph_left: float,
		yrs: float = 0.0,
		spent: float = 0.0,
		cost_left: float = 0.0,
		lab_left: Optional[Dict[str, float]] = None,
		hours_offered_this_year: Optional[float] = None,
		hours_directed_this_year: Optional[float] = None,
		hours_effective_this_year: Optional[float] = None,
		pool_total_this_year: Optional[float] = None,
		pool_active_count_this_year: Optional[int] = None,
		pool_rank_this_year: Optional[int] = None,
		pool_remaining_before_this_year: Optional[float] = None,
		stalled_years: Optional[int] = None,
		blocked_on_trades: Optional[List[str]] = None,
		underfunded_this_year: Optional[bool] = None,
		why_underfunded: Optional[str] = None,
		short_of_trade: Optional[List[str]] = None,
		waiting_on_money: Optional[bool] = None,
		paused: Optional[bool] = None,
		mothballed: Optional[bool] = None,
		_on_change: Optional[Callable[[], None]] = None,
		**kwargs: Any
	) -> None:
		super().__init__()
		self._on_change = None
		super().__setitem__("ph_left", ph_left)
		super().__setitem__("yrs", yrs)
		super().__setitem__("spent", spent)
		super().__setitem__("cost_left", cost_left)
		if lab_left is not None:
			super().__setitem__("lab_left", self._wrap_value(lab_left))
		if hours_offered_this_year is not None:
			super().__setitem__("hours_offered_this_year", hours_offered_this_year)
		if hours_directed_this_year is not None:
			super().__setitem__("hours_directed_this_year", hours_directed_this_year)
		if hours_effective_this_year is not None:
			super().__setitem__("hours_effective_this_year", hours_effective_this_year)
		if pool_total_this_year is not None:
			super().__setitem__("pool_total_this_year", pool_total_this_year)
		if pool_active_count_this_year is not None:
			super().__setitem__("pool_active_count_this_year", pool_active_count_this_year)
		if pool_rank_this_year is not None:
			super().__setitem__("pool_rank_this_year", pool_rank_this_year)
		if pool_remaining_before_this_year is not None:
			super().__setitem__("pool_remaining_before_this_year", pool_remaining_before_this_year)
		if stalled_years is not None:
			super().__setitem__("stalled_years", stalled_years)
		if blocked_on_trades is not None:
			super().__setitem__("blocked_on_trades", blocked_on_trades)
		if underfunded_this_year is not None:
			super().__setitem__("underfunded_this_year", underfunded_this_year)
		if why_underfunded is not None:
			super().__setitem__("why_underfunded", why_underfunded)
		if short_of_trade is not None:
			super().__setitem__("short_of_trade", short_of_trade)
		if waiting_on_money is not None:
			super().__setitem__("waiting_on_money", waiting_on_money)
		if paused is not None:
			super().__setitem__("paused", paused)
		if mothballed is not None:
			super().__setitem__("mothballed", mothballed)
		for k, v in kwargs.items():
			super().__setitem__(k, self._wrap_value(v))
		self._on_change = _on_change

	@classmethod
	def from_dict(cls, d: Dict[str, Any], _on_change: Optional[Callable[[], None]] = None) -> "ActiveProjectState":
		return cls(**d, _on_change=_on_change)

	def __getattribute__(self, name: str) -> Any:
		if name.startswith("_") or name in ("to_canon_dict", "from_dict", "_fire", "_wrap_value"):
			return super().__getattribute__(name)
		if dict.__contains__(self, name):
			return dict.__getitem__(self, name)
		if hasattr(type(self), name) and name not in type(self).__dataclass_fields__:
			return super().__getattribute__(name)
		if name in type(self).__dataclass_fields__:
			return None
		return super().__getattribute__(name)

	def __setattr__(self, name: str, value: Any) -> None:
		if name.startswith("_"):
			super().__setattr__(name, value)
		else:
			self[name] = value

	def __delattr__(self, name: str) -> None:
		if name.startswith("_"):
			super().__delattr__(name)
		else:
			self.pop(name, None)

	def to_canon_dict(self) -> Dict[str, Any]:
		"""Export state as a clean dictionary preserving active fields."""
		out: Dict[str, Any] = {}
		for k, v in self.items():
			if not k.startswith("_"):
				if isinstance(v, _InvalidatingDict):
					out[k] = dict(v)
				else:
					out[k] = v
		return out



@dataclass
class HouseholdState:
	"""The founder's household finances, standing staff, standing, and biographical history."""
	capital: float
	total_spend: float = 0.0
	bounties_paid: int = 0
	wages_paid: float = 0.0
	wages_prepaid: float = 0.0
	wages_earned: Optional[float] = None
	interest_paid: Optional[float] = None
	reputation: float = 5.0
	scandal: float = 0.0
	eminence: float = 0.0
	familiarity: float = 0.0
	protection: float = 0.0
	bribes_ytd: float = 0.0
	slaves: int = 0
	freedmen: int = 0
	manumitted_total: int = 0
	atrocity: int = 0
	bondage_years_left: float = 0.0
	bondage_debt: float = 0.0
	credit_frozen_until: int = 0
	insolvent_years: Optional[int] = None
	last_withdrawal: Optional[int] = None
	last_settlement: int = -999
	spend_last_year: Optional[float] = None

	# Workforce and human capital
	scholars: float = 0.0
	artisans: float = 0.0
	directors_extra: float = 0.0
	employees: Dict[str, float] = field(default_factory=dict)
	trades_created: Set[str] = field(default_factory=set)
	trades_endemic: Set[str] = field(default_factory=set)
	trade_introduced_year: Dict[str, int] = field(default_factory=dict)
	contract_hours: Dict[str, float] = field(default_factory=dict)
	commissioned: Dict[str, float] = field(default_factory=dict)
	teaching_hours_this_year: float = 0.0
	hour_allocations: Dict[str, float] = field(default_factory=dict)
	work_trade: Optional[str] = None
	last_taught: Dict[str, int] = field(default_factory=dict)
	training: List[List[Any]] = field(default_factory=list)
	wage_hours_this_year: Optional[float] = None
	log: List[Tuple[Any, str]] = field(default_factory=list)
	granted_staff: Optional[Dict[str, float]] = None
	hours_this_year: Optional[Dict[str, float]] = None
	trade_schools: Optional[int] = None
	worker_housing_places: Optional[int] = None
	_said_deputies: Optional[int] = None
	_said_near_limit: Optional[bool] = None
	_said_autoopen: Optional[Dict[str, int]] = None


@dataclass
class ProjectsState:
	"""Research projects, active engineering ventures, and technological capability."""
	active: Dict[str, ActiveProjectState] = field(default_factory=dict)
	done: Set[str] = field(default_factory=set)
	done_year: Optional[Dict[str, int]] = None
	operating: Set[str] = field(default_factory=set)
	failed_attempts: DefaultDict[str, int] = field(default_factory=lambda: collections.defaultdict(int))
	mothballed: Set[str] = field(default_factory=set)
	bountied: Set[str] = field(default_factory=set)
	granted: Set[str] = field(default_factory=set)
	opened_year: Dict[str, int] = field(default_factory=dict)
	paid_towards: Dict[str, float] = field(default_factory=dict)
	forgotten: Dict[str, int] = field(default_factory=dict)
	trade_hours_used: Dict[str, float] = field(default_factory=dict)
	revealed: Set[str] = field(default_factory=set)
	stalled: int = 0
	shut_for_staff: Optional[Dict[str, int]] = None


@dataclass
class EconomyState:
	"""Physical plants, extractive workings, durable inventory, and material flows."""
	mines: List[Dict[str, Any]] = field(default_factory=list)
	mine_pending: Dict[str, float] = field(default_factory=dict)
	mine_ready: Dict[str, int] = field(default_factory=dict)
	mine_cost_paid: float = 0.0
	mine_tranches: Optional[List[Any]] = None
	shortages: collections.Counter = field(default_factory=collections.Counter)
	throttle: float = 1.0
	binding: Optional[str] = None
	forest_ha: float = 0.0
	nitre_bed_m2: float = 0.0
	market_pressure: float = 0.0
	output_factor: float = 1.0
	economy: float = 1.0
	money_real: float = 1.0
	_material_stock_ledger: Optional[Dict[str, float]] = None
	farm_hectares: Optional[float] = None
	farm_stock_kg: float = 0.0
	_dashboard_history: Optional[List[Any]] = None


@dataclass
class GovernanceState:
	"""Institutions and civic administrative units."""
	inst_units: Optional[Dict[str, float]] = None
	gov: float = 0.0


@dataclass
class FounderState:
	"""Founder biology, lifespan, and personal capacity."""
	founder_alive: bool = True
	life_left: float = 40.0
	dead_reason: Optional[str] = None
	director_hours_spent_founder: float = 0.0
	living_cost_paid: float = 0.0
	policy: Dict[str, Any] = field(default_factory=dict)
	last_patron_death: Optional[int] = None
	_founder_death_aged: Optional[int] = None
	_founder_death_year: Optional[int] = None


@dataclass
class ScenarioState:
	"""Simulation scenario configuration and timeline."""
	year: int = 100
	goal_year: Optional[int] = None
	_said_debasement: Optional[int] = None
	_said_output: Optional[Dict[str, int]] = None
	_said_scandal: Optional[int] = None
	_said_parallelism: Optional[bool] = None
	_said_command_index: Optional[bool] = None


@dataclass
class PopulationState:
	"""World demography and agriculture state linkage."""
	pop_children: float = 0.0
	pop_working_age: float = 0.0
	pop_elderly: float = 0.0
	_food_pop_bonus_applied: Optional[float] = None


@dataclass
class SimulationState:
	"""Root coordinator aggregating authoritative persistent subsystem states."""
	household: HouseholdState
	projects: ProjectsState
	economy: Optional[EconomyState] = None
	governance: Optional[GovernanceState] = None
	founder: Optional[FounderState] = None
	scenario: Optional[ScenarioState] = None
	population: Optional[PopulationState] = None
	_civ: Optional[str] = None
	_goal: Optional[str] = None
	_civ_live: Dict[str, Any] = field(default_factory=dict)
	_weights: Dict[str, Any] = field(default_factory=dict)
	_fog: bool = False
	_immortal: bool = True
	_rng: Optional[List[Any]] = None
	_version: int = 3


ALL_STATE_CLASSES = (
	HouseholdState,
	ProjectsState,
	EconomyState,
	GovernanceState,
	FounderState,
	ScenarioState,
	PopulationState,
)


def get_save_fields() -> Tuple[str, ...]:
	"""Dynamically derive the save field names from authoritative state dataclasses."""
	fields: List[str] = []
	seen: Set[str] = set()
	for cls in ALL_STATE_CLASSES:
		for f in dataclasses.fields(cls):
			if not f.name.startswith("_on_change") and f.name not in seen:
				seen.add(f.name)
				fields.append(f.name)
	return tuple(fields)


SAVE_FIELDS = get_save_fields()


def serialize_state(obj: Any) -> Any:
	"""Recursively serialize authoritative simulation state to JSON-compatible data."""
	if obj is None or isinstance(obj, (int, float, str, bool)):
		return obj
	if hasattr(obj, "to_canon_dict"):
		return serialize_state(obj.to_canon_dict())
	if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
		out = {}
		for f in dataclasses.fields(obj):
			if f.name.startswith("_on_change"):
				continue
			val = getattr(obj, f.name)
			out[f.name] = serialize_state(val)
		if isinstance(obj, SimulationState):
			out["_version"] = 3
		return out
	from sim.engine.economy import _InvalidatingSet
	if isinstance(obj, (set, _InvalidatingSet)):
		return {"__set__": sorted(serialize_state(x) for x in obj)}
	import collections
	if isinstance(obj, (dict, _InvalidatingDict, collections.defaultdict, collections.Counter)):
		return {str(k): serialize_state(v) for k, v in obj.items() if not str(k).startswith("_on_change")}
	if isinstance(obj, (list, tuple)):
		return [serialize_state(x) for x in obj]
	return obj





def _deserialize_typed(val: Any, target_type: Any) -> Any:
	"""Recursively reconstruct typed values from JSON-compatible data according to target_type."""
	if val is None or target_type is Any:
		return val

	origin = get_origin(target_type)
	args = get_args(target_type)

	# Handle Union / Optional (Union[T, None])
	if origin is Union:
		non_none = [a for a in args if a is not type(None)]
		if not non_none:
			return val
		return _deserialize_typed(val, non_none[0])

	# Handle Set[T]
	if origin in (set, Set) or target_type in (set, Set):
		items = val.get("__set__") if isinstance(val, dict) else val
		if not isinstance(items, (list, set, tuple)):
			return set()
		elem_t = args[0] if args else None
		if elem_t and elem_t is not Any:
			return set(_deserialize_typed(x, elem_t) for x in items)
		return set(items)

	# Handle collections.Counter
	if target_type is collections.Counter or origin is collections.Counter:
		if isinstance(val, dict):
			return collections.Counter({k: int(v) for k, v in val.items()})
		return collections.Counter(val)

	# Handle collections.defaultdict / DefaultDict[K, V]
	if target_type is collections.defaultdict or origin in (collections.defaultdict, DefaultDict):
		val_t = args[1] if (args and len(args) > 1) else int
		default_factory = int
		if val_t in (float, "float"):
			default_factory = float
		elif val_t in (list, "list", List):
			default_factory = list
		elif val_t in (dict, "dict", Dict):
			default_factory = dict
		if isinstance(val, dict):
			return collections.defaultdict(default_factory, {
				k: _deserialize_typed(v, val_t) for k, v in val.items()
			})
		return collections.defaultdict(default_factory, val)

	# Handle ActiveProjectState
	if target_type is ActiveProjectState or (isinstance(target_type, type) and issubclass(target_type, ActiveProjectState)):
		if isinstance(val, dict):
			hints = {}
			try:
				hints = get_type_hints(ActiveProjectState)
			except Exception:
				hints = {}
			reconstructed = {}
			for f in dataclasses.fields(ActiveProjectState):
				if f.name in val:
					f_type = hints.get(f.name, f.type)
					reconstructed[f.name] = _deserialize_typed(val[f.name], f_type)
			for k, v in val.items():
				if k not in reconstructed and not str(k).startswith("_on_change"):
					reconstructed[k] = v
			return ActiveProjectState.from_dict(reconstructed)
		return val

	# Handle Dataclasses
	if dataclasses.is_dataclass(target_type) and isinstance(target_type, type):
		if not isinstance(val, dict):
			return val
		hints = {}
		try:
			hints = get_type_hints(target_type)
		except Exception:
			hints = {}
		field_kwargs = {}
		for f in dataclasses.fields(target_type):
			if f.name.startswith("_on_change"):
				continue
			if f.name in val:
				f_type = hints.get(f.name, f.type)
				field_kwargs[f.name] = _deserialize_typed(val[f.name], f_type)
		return target_type(**field_kwargs)

	# Handle List[T]
	if origin in (list, List) or target_type in (list, List):
		if not isinstance(val, (list, tuple)):
			return list(val) if val is not None else []
		elem_t = args[0] if args else None
		if elem_t and elem_t is not Any:
			return [_deserialize_typed(x, elem_t) for x in val]
		return list(val)

	# Handle Tuple[...]
	if origin in (tuple, Tuple) or target_type in (tuple, Tuple):
		if not isinstance(val, (list, tuple)):
			return tuple(val) if val is not None else ()
		if args:
			if len(args) == 2 and args[1] is Ellipsis:
				return tuple(_deserialize_typed(x, args[0]) for x in val)
			return tuple(_deserialize_typed(x, arg_t) for x, arg_t in zip(val, args))
		return tuple(val)

	# Handle Dict[K, V]
	if origin in (dict, Dict) or target_type in (dict, Dict):
		if not isinstance(val, dict):
			return val
		key_t = args[0] if args else None
		val_t = args[1] if (args and len(args) > 1) else None
		if (val_t and val_t is not Any) or (key_t and key_t is not Any):
			return {
				(_deserialize_typed(k, key_t) if key_t else k):
				(_deserialize_typed(v, val_t) if val_t else v)
				for k, v in val.items()
			}
		return dict(val)

	# Primitive scalars
	if target_type is int and isinstance(val, (int, float, str)) and not isinstance(val, bool):
		try:
			return int(val)
		except (ValueError, TypeError):
			return val
	if target_type is float and isinstance(val, (int, float, str)) and not isinstance(val, bool):
		try:
			return float(val)
		except (ValueError, TypeError):
			return val
	if target_type is str and not isinstance(val, str):
		return str(val)
	if target_type is bool:
		if isinstance(val, bool):
			return val
		if isinstance(val, str):
			return val.lower() in ("true", "1")
		if isinstance(val, (int, float)):
			return bool(val)
		return val

	return val


def deserialize_state(blob: Any, target_type: Optional[type] = None) -> Any:
	"""Reconstruct typed authoritative state objects from JSON-compatible data."""
	if blob is None:
		return None
	if target_type is None:
		if isinstance(blob, dict) and ("_version" in blob or "household" in blob):
			target_type = SimulationState
		elif isinstance(blob, dict) and "ph_left" in blob:
			target_type = ActiveProjectState
		else:
			return blob

	return _deserialize_typed(blob, target_type)



def _safe_get(sim: Any, k: str) -> Any:
	"""Safely get attribute value from household or sim without raising AttributeError for lazy fields."""
	if hasattr(sim.household, k):
		return getattr(sim.household, k)
	if hasattr(sim, k):
		return getattr(sim, k)
	return None


def extract_simulation_state(sim: Any) -> SimulationState:
	"""Extract typed authoritative simulation state from a running Sim instance."""
	hh_fields = {f.name for f in dataclasses.fields(HouseholdState)}
	proj_fields = {f.name for f in dataclasses.fields(ProjectsState)}
	econ_fields = {f.name for f in dataclasses.fields(EconomyState)}
	gov_fields = {f.name for f in dataclasses.fields(GovernanceState)}
	fnd_fields = {f.name for f in dataclasses.fields(FounderState)}
	scen_fields = {f.name for f in dataclasses.fields(ScenarioState)}
	pop_fields = {f.name for f in dataclasses.fields(PopulationState)}

	hh_data = {k: _safe_get(sim, k) for k in hh_fields}
	proj_data = {k: _safe_get(sim, k) for k in proj_fields}
	econ_data = {k: _safe_get(sim, k) for k in econ_fields}
	gov_data = {k: _safe_get(sim, k) for k in gov_fields}
	fnd_data = {k: _safe_get(sim, k) for k in fnd_fields}
	scen_data = {k: _safe_get(sim, k) for k in scen_fields}
	pop_data = {k: _safe_get(sim, k) for k in pop_fields}

	try:
		rng_state = sim.rng.getstate()
		rng_val = [rng_state[0], list(rng_state[1]), rng_state[2]]
	except Exception:
		rng_val = None

	return SimulationState(
		household=HouseholdState(**hh_data),
		projects=ProjectsState(**proj_data),
		economy=EconomyState(**econ_data),
		governance=GovernanceState(**gov_data),
		founder=FounderState(**fnd_data),
		scenario=ScenarioState(**scen_data),
		population=PopulationState(**pop_data),
		_civ=sim.civ.get("id"),
		_goal=sim.goal,
		_civ_live={attr: sim.civ.get(attr) for attr in ("literacy_general", "literacy_elite", "state_capacity")},
		_weights=dict(sim.value_weights),
		_fog=sim.fog,
		_immortal=bool(sim.cfg.get("immortal", True)),
		_rng=rng_val,
		_version=3,
	)


def apply_simulation_state(state: SimulationState, sim: Any) -> None:
	"""Apply deserialized authoritative state to a Sim instance and restore runtime wrappers."""
	import collections
	if state.household:
		for f in dataclasses.fields(state.household):
			val = getattr(state.household, f.name)
			if val is not None:
				setattr(sim.household, f.name, val)
				setattr(sim, f.name, val)

	if state.projects:
		for f in dataclasses.fields(state.projects):
			val = getattr(state.projects, f.name)
			if val is not None:
				if hasattr(sim.household, f.name):
					setattr(sim.household, f.name, val)
				setattr(sim, f.name, val)

	if state.economy:
		for f in dataclasses.fields(state.economy):
			val = getattr(state.economy, f.name)
			if val is not None:
				setattr(sim, f.name, val)

	if state.governance:
		for f in dataclasses.fields(state.governance):
			val = getattr(state.governance, f.name)
			if val is not None:
				setattr(sim, f.name, val)

	if state.founder:
		for f in dataclasses.fields(state.founder):
			val = getattr(state.founder, f.name)
			if val is not None:
				setattr(sim, f.name, val)

	if state.scenario:
		for f in dataclasses.fields(state.scenario):
			val = getattr(state.scenario, f.name)
			if val is not None:
				setattr(sim, f.name, val)
				if hasattr(sim.household, f.name):
					setattr(sim.household, f.name, val)

	if state.population:
		for f in dataclasses.fields(state.population):
			val = getattr(state.population, f.name)
			if val is not None:
				setattr(sim, f.name, val)

	# Restore runtime invalidating wrappers and callbacks
	from sim.engine.economy import _InvalidatingDict, _InvalidatingSet
	op_val = sim.household.operating if (hasattr(sim.household, "operating") and sim.household.operating is not None) else set()
	sim.household.operating = _InvalidatingSet(op_val, on_change=sim._operating_changed)
	act_val = sim.household.active if (hasattr(sim.household, "active") and sim.household.active is not None) else {}
	sim.household.active = _InvalidatingDict(
		{k: ActiveProjectState.from_dict(v if isinstance(v, dict) else v.to_canon_dict(), _on_change=sim._active_changed)
		 for k, v in act_val.items()},
		on_change=sim._active_changed
	)
	emp_val = sim.household.employees if (hasattr(sim.household, "employees") and sim.household.employees is not None) else {}
	sim.household.employees = _InvalidatingDict(emp_val, on_change=sim._workforce_changed)
	fa_val = getattr(sim, "failed_attempts", None) or getattr(sim.household, "failed_attempts", None) or {}
	sim.failed_attempts = collections.defaultdict(
		int, {node_id: int(value) for node_id, value in fa_val.items()}
	)
	sh_val = getattr(sim, "shortages", None) or getattr(sim.household, "shortages", None) or {}
	sim.shortages = collections.Counter(sh_val)

	if state._fog is not None:
		sim.fog = bool(state._fog)
	if state._immortal is not None:
		sim.cfg["immortal"] = bool(state._immortal)
	if state._goal is not None:
		sim.goal = state._goal
	if state._rng is not None:
		rng_version, _keys, rng_gaussian = state._rng
		sim.rng.setstate((rng_version, tuple(int(state_int) for state_int in _keys), rng_gaussian))
	if state._civ_live:
		for attr, value in state._civ_live.items():
			if value is not None:
				sim.civ[attr] = value
	if state._weights:
		sim.value_weights.update(state._weights)
	sim.state_capacity = float(sim.civ.get("state_capacity", sim.state_capacity))

	# Clean transient caches and increment version counters
	sim._reset_economic_caches()
