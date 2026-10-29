"""Authoritative simulation state definitions and explicit subsystem state owners.

Every persistent mutable field in the simulation belongs to one authoritative
state owner defined in this module. Transient caches, version counters, derived
values, and invalidation plumbing remain non-persistent implementation details.
"""
import collections
import contextlib
import dataclasses
from dataclasses import InitVar, dataclass, field
from typing import (
	TYPE_CHECKING, Any, Callable, DefaultDict, Dict, List,
	Optional, Set, Tuple, Union, get_args, get_origin, get_type_hints,
)

from sim.agents.api import ActorRecord, ActorsState, Business  # noqa: F401
from sim.engine.state_holdings import HoldingsState, SeatProgressState
from sim.invalidating import ActiveProjectState, _InvalidatingDict
from sim.refusal import Refusal, as_record, from_record, is_record

if TYPE_CHECKING:
	from sim.engine.state_seat import SeatState  # set on this module at import by state_seat


@dataclass
class HouseholdState:
	"""The founder's household's standing staff, standing, and biographical history (its money is the ledger's)."""
	# a planned project and the cash target put by for it (`saving`)
	saving_for: Optional[str] = None
	saving_target: float = 0.0


@dataclass
class EconomyState:
	"""Physical plants, extractive workings, durable inventory, and material flows."""
	# the money an hour of work was worth when the tree's money fields were last counted (opening_money.py)
	nodes_money_per_labour_hour: Optional[float] = None


@dataclass
class FounderState:
	"""What the interface remembers of the founder's death (the founder's life and policy are the seats module's)."""
	_founder_death_aged: Optional[int] = None
	_founder_death_year: Optional[int] = None


@dataclass
class SimulationState:
	"""Root coordinator aggregating authoritative persistent subsystem states."""
	# household, holdings, seat_progress and founder only build the first seat when `seats` is empty; they are not kept
	household: InitVar[Optional[HouseholdState]] = None
	economy: Optional[EconomyState] = None
	holdings: InitVar[Optional[HoldingsState]] = None
	seat_progress: InitVar[Optional[SeatProgressState]] = None
	founder: InitVar[Optional[FounderState]] = None
	seats: Dict[str, "SeatState"] = field(default_factory=dict)
	acting_seat: str = "founder"
	_civ: Optional[str] = None
	_immortal: bool = True
	_rng: Optional[List[Any]] = None
	_seed: Optional[Union[int, str]] = None
	_game_version: Optional[str] = None  # which build wrote the save; shown to people, never checked on load
	modules: Dict[str, Any] = field(default_factory=dict)          # module id -> its world state (sim/assembly slots)
	assembly_record: Dict[str, Any] = field(default_factory=dict)  # which modules, layers and mods wrote this game
	interface: Dict[str, Any] = field(default_factory=dict)  # the UI's own memory; the engine never reads it

	def __post_init__(self, household, holdings, seat_progress, founder) -> None:
		from sim.engine.state_seat import FIRST_SEAT_ID, SeatState
		if not self.seats:   # built from the objects directly: they become the first seat
			self.acting_seat = FIRST_SEAT_ID
			given = {"holdings": holdings, "seat_progress": seat_progress}
			self.seats[FIRST_SEAT_ID] = SeatState(
				household, founder, **{name: value for name, value in given.items() if value is not None})

	@property
	def acting_record(self) -> "SeatState":
		"""The acting seat's record: its household, founder, holdings and progress."""
		return self.seats[self.acting_seat]

	@property
	def actors(self) -> Optional[ActorsState]:
		"""The actors' records: the actors module's world slot (None before the assembly has made it; a save read back holds
		it as plain data until the module set revives it)."""
		held = self.modules.get("actors")
		return held if isinstance(held, ActorsState) else None

	@actors.setter
	def actors(self, value: Optional[ActorsState]) -> None:
		self.modules["actors"] = value


for _build_only in ("household", "holdings", "seat_progress", "founder"):
	delattr(SimulationState, _build_only)   # a build argument leaves no attribute to read: a stale reader raises


ALL_STATE_CLASSES = (
	HouseholdState,
	EconomyState,
	FounderState,
	HoldingsState,
	SeatProgressState,
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


_PLAIN_SCALARS = frozenset((int, float, str, bool))


# Containers already plain JSON (string keys, scalars, lists, dicts) that serialize_state hands back
# untouched, so the encoder meets them directly; held only while a save runs.
_VERBATIM = []


@contextlib.contextmanager
def verbatim(*containers):
	"""Within the block serialize_state returns these (already plain JSON) containers as they are."""
	held = [container for container in containers if container is not None]
	_VERBATIM.extend(held)
	try:
		yield
	finally:
		del _VERBATIM[len(_VERBATIM) - len(held):]


def serialize_state(obj: Any) -> Any:
	"""Recursively serialize authoritative simulation state to JSON-compatible data."""
	kind = type(obj)
	if obj is None or kind in _PLAIN_SCALARS:
		return obj
	if kind is dict:   # the plain containers need none of the checks below
		if _VERBATIM and any(obj is held for held in _VERBATIM):
			return obj
		return {str(k): serialize_state(v) for k, v in obj.items() if not str(k).startswith("_on_change")}
	if kind is list or kind is tuple:
		return [serialize_state(x) for x in obj]
	if isinstance(obj, Refusal):   # a coded line keeps its code, choices and facts across a save
		record = as_record(obj)
		return {key: serialize_state(value) for key, value in record.items()}
	if isinstance(obj, (int, float, str, bool)):
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
	from sim.invalidating import _InvalidatingSet
	if isinstance(obj, (set, _InvalidatingSet)):
		return {"__set__": sorted(serialize_state(x) for x in obj)}
	if isinstance(obj, (dict, _InvalidatingDict, collections.defaultdict, collections.Counter)):
		return {str(k): serialize_state(v) for k, v in obj.items() if not str(k).startswith("_on_change")}
	if isinstance(obj, (list, tuple)):
		return [serialize_state(x) for x in obj]
	return obj





def _deserialize_typed(val: Any, target_type: Any) -> Any:
	"""Recursively reconstruct typed values from JSON-compatible data according to target_type."""
	if is_record(val):
		return from_record(val)
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
