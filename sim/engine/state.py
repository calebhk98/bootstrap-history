"""Authoritative simulation state definitions and explicit subsystem state owners.

Every persistent mutable field in the simulation belongs to one authoritative
state owner defined in this module. Transient caches, version counters, derived
values, and invalidation plumbing remain non-persistent implementation details.
"""
import collections
import dataclasses
from dataclasses import dataclass, field
from typing import (
	TYPE_CHECKING, Any, Callable, DefaultDict, Dict, List,
	Optional, Set, Tuple, Union, get_args, get_origin, get_type_hints,
)

from sim.agents.api import ActorRecord, ActorsState, CapitalMarketRecord  # noqa: F401
from sim.engine import cash_book
from sim.engine.state_holdings import HoldingsState, SeatProgressState
from sim.invalidating import ActiveProjectState, _InvalidatingDict

if TYPE_CHECKING:
	from sim.engine.state_seat import SeatState  # set on this module at import by state_seat


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
	scandal_last_year: Optional[float] = None
	eminence: float = 0.0
	familiarity: float = 0.0
	protection: float = 0.0
	# how the household answers the state's demands: "comply" or "refuse" (sim/agents/demand_answer.py)
	demand_stance: str = "comply"
	bribes_ytd: float = 0.0
	slaves: int = 0
	freedmen: int = 0
	manumitted_total: int = 0
	atrocity: int = 0
	bondage_years_left: float = 0.0
	bondage_debt: float = 0.0
	credit_frozen_until: int = 0
	insolvent_years: int = 0
	last_withdrawal: Optional[int] = None
	last_settlement: int = -999
	spend_last_year: Optional[float] = None
	# the cash book (sim/engine/cash_book.py): the open period's entries by cause, cash at its start,
	# and the last few closed years
	cash_flow: Dict[str, float] = field(default_factory=dict)
	cash_mark: Optional[float] = None
	cash_periods: List[Dict[str, Any]] = field(default_factory=list)
	# the cause book (sim/engine/cause_book.py): rows for wage, notice and closure changes, and the readings they are measured from
	cause_rows: List[Dict[str, Any]] = field(default_factory=list)
	cause_mark: Optional[Dict[str, float]] = None

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
	relocation_hours_this_year: float = 0.0
	base_tile: Optional[str] = None
	hour_allocations: Dict[str, float] = field(default_factory=dict)
	# standing order id -> [hours ordered, shortfall kind] last reported as unused, so repeats stay quiet
	unused_hours_reported: Dict[str, List[Any]] = field(default_factory=dict)
	work_trade: Optional[str] = None
	last_taught: Dict[str, int] = field(default_factory=dict)
	training: List[List[Any]] = field(default_factory=list)
	wage_hours_this_year: float = 0.0
	wage_income_this_year: float = 0.0
	wage_work_last_year: Optional[Dict[str, float]] = None
	log: List[Tuple[Any, str]] = field(default_factory=list)
	granted_staff: Optional[Dict[str, float]] = None
	hours_this_year: Optional[Dict[str, float]] = None
	trade_schools: Optional[int] = None
	labour_pressure_records: Dict[str, Any] = field(default_factory=dict)
	worker_housing_places: Optional[int] = None
	# spare generic hands the reserve_staff policy keeps above what concerns hold (`reserve`)
	reserve_craftsmen: int = 0
	reserve_scholars: int = 0
	# a planned project and the cash target put by for it (`saving`)
	saving_for: Optional[str] = None
	saving_target: float = 0.0
	# what the automatic policies did in the last few years (`automation`)
	automation_audit: List[Any] = field(default_factory=list)
	_said_deputies: int = 0
	_said_near_limit: Optional[bool] = None
	_said_autoopen: Optional[Dict[str, int]] = None
	_said_eminence: int = -999
	_said_requisition: int = -999
	_said_notice_approach: int = 0
	last_military_demand: int = -999
	_said_confiscation_band: int = -1

	def credit(self, amount: float, purpose: Any) -> None:
		"""Money in, entered in the cash book under its cause."""
		self.capital += float(amount)
		cash_book.record(self, 1.0, float(amount), purpose)

	def debit(self, amount: float, purpose: Any) -> None:
		"""Money out, entered in the cash book under its cause."""
		self.capital -= float(amount)
		cash_book.record(self, -1.0, float(amount), purpose)

	def reset_cash(self, new_capital: float, purpose: Any) -> None:
		"""Set the purse to an exact figure (a settlement), entering the difference under its cause."""
		difference = new_capital - self.capital
		self.capital = new_capital
		cash_book.record(self, 1.0, difference, purpose)

	def cost_capital(self, amount: float, purpose: Any = "expenditure") -> None:
		"""Pay out of the purse and track total spend."""
		self.debit(amount, purpose)
		self.total_spend += float(amount)

	def costCapital(self, amount: float, purpose: Any = "expenditure") -> None:
		"""Alias for cost_capital following camelCase convention."""
		self.cost_capital(amount, purpose)

	def add_capital(self, amount: float, purpose: Any = "receipts") -> None:
		"""Credit capital into household purse."""
		self.credit(amount, purpose)

	def add_reputation(self, delta: float) -> None:
		"""Increase household reputation standing."""
		self.reputation += float(delta)

	def deduct_reputation(self, delta: float) -> None:
		"""Decrease household reputation standing."""
		self.reputation -= float(delta)

	def add_scandal(self, delta: float) -> None:
		"""Increase accumulated scandal."""
		self.scandal += float(delta)

	def record_spend(self, amount: float) -> None:
		"""Record spend without altering capital balance directly."""
		self.total_spend += float(amount)


@dataclass
class ProjectsState:
	"""Research projects, active engineering ventures, and technological capability."""
	active: Dict[str, ActiveProjectState] = field(default_factory=dict)
	done: Set[str] = field(default_factory=set)
	done_year: Optional[Dict[str, int]] = None
	operating: Set[str] = field(default_factory=set)
	failed_attempts: DefaultDict[str, int] = field(default_factory=lambda: collections.defaultdict(int))
	uninformed_failures: Dict[str, int] = field(default_factory=dict)
	# technique -> retained worker-years of anyone running it (industry_depth.py)
	industry_years: Dict[str, float] = field(default_factory=dict)
	industry_seeded: bool = False
	# technique -> worker-years a year the society's opening producers put in (industry_depth.py)
	industry_opening_rate: Dict[str, float] = field(default_factory=dict)
	mothballed: Set[str] = field(default_factory=set)
	bountied: Set[str] = field(default_factory=set)
	granted: Set[str] = field(default_factory=set)
	opened_year: Dict[str, int] = field(default_factory=dict)
	paid_towards: Dict[str, float] = field(default_factory=dict)
	forgotten: Dict[str, int] = field(default_factory=dict)
	trade_hours_used: Dict[str, float] = field(default_factory=dict)
	revealed: Set[str] = field(default_factory=set)
	# node id -> what the founder chose to do with the invention: {"mode", "published_year",
	# "licensees": {actor id -> {"fee", "royalty", "year"}}}; a node absent from it is on the default
	disclosures: Dict[str, Dict[str, Any]] = field(default_factory=dict)
	# concerns whose staff the yearly step hires for before the closure rule (`keep <id> staffed`)
	keep_staffed: Set[str] = field(default_factory=set)
	# node ids, `category:<cat>` and `trait:<trait>` the automatic starters (rush, auto_open, auto_commission) skip
	excluded: Set[str] = field(default_factory=set)
	stalled: int = 0
	# work id -> {"reason": str, "year": int}; only while the work is mothballed
	closures: Dict[str, Dict[str, object]] = field(default_factory=dict)
	# every work ever shut for want of staff; kept after it reopens
	ever_closed_for_staff: Set[str] = field(default_factory=set)
	# this year's staffing closures and reopenings: year, closed, reopened, short (resource -> amount)
	staffing_tally: Dict[str, object] = field(default_factory=dict)

	def active_keys_sorted(self) -> List[str]:
		"""Return active project ids in the canonical resolution order.

		Callers that aggregate or mutate project state must not inherit dict
		insertion order from a save file or command history.
		"""
		return sorted(self.active)

	def operating_keys_sorted(self) -> List[str]:
		"""Return operating project ids independently of set/hash order."""
		return sorted(self.operating)

	def done_keys_sorted(self) -> List[str]:
		"""Return completed project ids independently of set/hash order."""
		return sorted(self.done)


@dataclass
class EconomyState:
	"""Physical plants, extractive workings, durable inventory, and material flows."""
	# edge key (a port: tile id) -> {way: true} of the roads, track, canals, bridges and ports built (ways.py); geography's routes read it
	improvements: Dict[str, Dict[str, bool]] = field(default_factory=dict)
	# the same key -> {way: {due year, crew trade and hours a year, engineered, year last pressed}} of the ways paid for and being built (ways.py)
	ways_under_construction: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)
	# tile -> {construction node id: capacity built there} (works.py)
	works: Dict[str, Dict[str, float]] = field(default_factory=dict)
	# tile -> {construction node id: [year it is finished, capacity]} of works paid for and being built (works.py)
	works_under_construction: Dict[str, Dict[str, List[float]]] = field(default_factory=dict)
	agent_economy: Dict[str, Any] = field(default_factory=dict)   # the agent economy's record (economy_port_year.py)
	output_factor: float = 1.0
	# real output per person over the opening's, measured when the market closes (real_output.py)
	output_per_head: float = 1.0
	# material -> its price in labour hours the first year households were offered it, which values it in real output
	introduction_prices: Dict[str, float] = field(default_factory=dict)
	money_real: float = 1.0
	# commodity -> society capacity, stock and last price ratio (market_clearing.py)
	market_book: Dict[str, Dict[str, float]] = field(default_factory=dict)
	# the year's purchases and sales by commodity and party, and the founder's draws (goods_market_api.py)
	market_flows: Optional[Dict[str, Any]] = None
	# foreign economy id -> commodity -> its capacity, stock and price ratio (foreign_economies.py)
	foreign_market_book: Dict[str, Dict[str, Dict[str, float]]] = field(default_factory=dict)
	# foreign economy id -> material -> tonnes actors carried to and from it this year (foreign_actor_trade.py)
	foreign_actor_trade: Dict[str, Dict[str, Dict[str, float]]] = field(default_factory=dict)
	# material -> tonnes actors landed in the home market and took from it this year (foreign_actor_trade.py)
	home_actor_trade: Dict[str, Dict[str, float]] = field(default_factory=dict)
	# material -> the market price ratio wages read, as of the last year's close (wage_market_ratios.py)
	wage_market_ratios: Dict[str, float] = field(default_factory=dict)
	# coin metal -> the market's price over the incumbents' cost at the last year's close (coin_revaluation.py)
	coin_metal_ratios: Dict[str, float] = field(default_factory=dict)
	# foreign economy id -> goods and coin paid, and the route's lift (foreign_payments.py)
	foreign_ledger: Dict[str, Dict[str, float]] = field(default_factory=dict)
	capacity_pool: Dict[str, float] = field(default_factory=dict)
	# year -> value of goods this society imported ("in") and exported ("out") that year, in its money;
	# the state's customs read the last completed year (foreign_payments.py)
	foreign_trade_by_year: Dict[str, Dict[str, float]] = field(default_factory=dict)
	society_labour_hours: Dict[str, float] = field(default_factory=dict)
	wage_tightness_factors: Dict[str, float] = field(default_factory=dict)


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
	weather_salt: int = 0     # this game's own weather history, drawn from its dice (Complaint 384)
	_said_debasement: Optional[int] = None
	_said_output: Optional[Dict[str, int]] = None
	_said_wage_cascade: int = -999    # last year a wage-cascade note was printed
	_literacy_said: int = -999        # last year a literacy-census note was printed
	_said_condition: Set[str] = field(default_factory=set)  # hazard-condition messages already printed once


@dataclass
class PopulationState:
	"""World demography and agriculture state linkage."""
	pop_children: float = 0.0
	pop_working_age: float = 0.0
	pop_elderly: float = 0.0
	population_change_last_year: Optional[float] = None
	# one dict per simulated year: year, population, births, deaths, nutrition_ratio
	yearly_record: List[Any] = field(default_factory=list)


@dataclass
class SimulationState:
	"""Root coordinator aggregating authoritative persistent subsystem states."""
	# household, projects, founder, governance, holdings and seat_progress alias the acting seat's objects and are not saved (seats are)
	household: Optional[HouseholdState] = field(default=None, metadata={"alias": True})
	projects: Optional[ProjectsState] = field(default=None, metadata={"alias": True})
	economy: Optional[EconomyState] = None
	governance: Optional[GovernanceState] = field(default=None, metadata={"alias": True})
	holdings: Optional[HoldingsState] = field(default=None, metadata={"alias": True})
	seat_progress: Optional[SeatProgressState] = field(default=None, metadata={"alias": True})
	founder: Optional[FounderState] = field(default=None, metadata={"alias": True})
	seats: Dict[str, "SeatState"] = field(default_factory=dict)
	acting_seat: str = "founder"
	scenario: Optional[ScenarioState] = None
	population: Optional[PopulationState] = None
	actors: Optional[ActorsState] = None
	_civ: Optional[str] = None
	_civ_live: Dict[str, Any] = field(default_factory=dict)
	_weights: Dict[str, Any] = field(default_factory=dict)
	_fog: bool = False
	_fuzzy_estimates: bool = False
	_fuzzy_salt: int = 0
	_immortal: bool = True
	_rng: Optional[List[Any]] = None
	_seed: Optional[Union[int, str]] = None
	interface: Dict[str, Any] = field(default_factory=dict)  # the UI's own memory; the engine never reads it

	def __post_init__(self) -> None:
		from sim.engine.state_seat import FIRST_SEAT_ID, SeatState, bind_seat
		if not self.seats:   # built from the three objects directly: they become the first seat
			self.acting_seat = FIRST_SEAT_ID
			given = {name: getattr(self, name) for name in ("governance", "holdings", "seat_progress")}
			self.seats[FIRST_SEAT_ID] = SeatState(
				self.household, self.projects, self.founder,
				**{name: value for name, value in given.items() if value is not None})
		bind_seat(self, self.acting_seat)

	@property
	def _goal(self) -> Optional[str]:
		return self.seats[self.acting_seat].goal

	@_goal.setter
	def _goal(self, value: Optional[str]) -> None:
		self.seats[self.acting_seat].goal = value


ALL_STATE_CLASSES = (
	HouseholdState,
	ProjectsState,
	EconomyState,
	GovernanceState,
	FounderState,
	HoldingsState,
	SeatProgressState,
	ScenarioState,
	PopulationState,
	ActorsState,
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
			if f.name.startswith("_on_change") or f.metadata.get("alias"):
				continue
			val = getattr(obj, f.name)
			out[f.name] = serialize_state(val)
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
		if not isinstance(blob, dict):
			return blob
		target_type = ActiveProjectState if "ph_left" in blob else SimulationState

	return _deserialize_typed(blob, target_type)


from sim.engine import state_seat  # noqa: E402,F401  (registers SeatState, which needs the classes above)
