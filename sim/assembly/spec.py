"""What a module declares: its state, the views it publishes, the commands it applies, what it reads and sends."""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple

from .kernels import Kernel

TABLE = "table"        # one whole value: `needs.name()`
KEYED = "keyed"        # one value per key, computed on first read of that key: `needs.name[key]`
QUOTE = "quote"        # a question with arguments, never cached: `needs.name(*arguments)`

SUM = "sum"            # extension point answers added together
FIRST = "first"        # the first answer that is not None, in mod load order
LIST = "list"          # every answer, in mod load order


@dataclass(frozen=True)
class ViewSpec:
	name: str
	compute: str                                  # method name on the module that computes it
	kind: str = TABLE
	channels: Tuple[str, ...] = ()                # the owner's version channels the value depends on
	inputs: Tuple[str, ...] = ()                  # other views the value depends on (they must be in the owner's reads)
	seat_scoped: bool = False                     # the value is the acting seat's
	cached: bool = True                           # False while the owner does not yet bump its channels on every write


@dataclass(frozen=True)
class ExtensionPoint:
	name: str
	combine: str = LIST


@dataclass(frozen=True)
class Provision:
	"""A shipped module's answer to an extension point: `method` on the module, known to mods as
	`<module_id>.<name>` (the name a mod withdraws it by)."""
	point: str
	method: str
	name: str


@dataclass(frozen=True)
class PhaseHook:
	name: str                                     # a name in the year's phase list (sim/engine/year_phases.py)
	method: str


@dataclass(frozen=True)
class Command:
	"""Base of every command: a typed request to the owner of a fact. Subclasses are frozen dataclasses."""


@dataclass(frozen=True)
class ModuleSpec:
	module_id: str
	implementation: type
	channels: Tuple[str, ...] = ()                # version channels the owner bumps when its state changes
	world_state: Optional[type] = None            # dataclass saved once per game
	seat_state: Optional[type] = None             # dataclass saved once per seat, rebound by act_as
	publishes: Tuple[ViewSpec, ...] = ()
	applies: Tuple[Tuple[type, str], ...] = ()    # (command class, handler method name)
	reads: Tuple[str, ...] = ()                   # views and extension points it uses; assembly fails without a provider
	optional_reads: Tuple[str, ...] = ()          # used when provided; None when nothing provides them
	sends: Tuple[type, ...] = ()                  # command classes it may send
	phases: Tuple[PhaseHook, ...] = ()
	extension_points: Tuple[ExtensionPoint, ...] = ()
	provides: Tuple[Provision, ...] = ()          # answers to extension points (its own or other modules')
	kernels: Tuple[Kernel, ...] = ()              # computations a mod may replace (Complaint 661), each named `<module_id>.<name>`


@dataclass
class Operations:
	"""What one mod asks of the assembly, collected by its `register(api)`."""
	mod_id: str
	added: Tuple[ModuleSpec, ...] = ()
	replaced: Dict[str, ModuleSpec] = field(default_factory=dict)
	removed: Tuple[str, ...] = ()
	layers: Dict[str, Tuple[type, ...]] = field(default_factory=dict)              # module id -> classes over it
	adjusters: Dict[str, Tuple[Tuple[Callable, Tuple[str, ...]], ...]] = field(default_factory=dict)  # view -> (function, reads)
	provided: Dict[str, Tuple[Callable, ...]] = field(default_factory=dict)        # extension point -> functions
	withdrawn: Tuple[str, ...] = ()                                                # "<module_id>.<name>" provisions taken out
	phases: Tuple[Any, ...] = ()                                                   # year phases the engine places (it owns their shape)
	kernels: Dict[str, Callable] = field(default_factory=dict)                     # kernel name -> the replacement function


def view_names(spec: ModuleSpec) -> Tuple[str, ...]:
	return tuple(view.name for view in spec.publishes)


def point_names(spec: ModuleSpec) -> Tuple[str, ...]:
	return tuple(point.name for point in spec.extension_points)


def handler_of(spec: ModuleSpec) -> Dict[type, str]:
	return dict(spec.applies)


def declared_methods(spec: ModuleSpec) -> Tuple[str, ...]:
	"""The methods other parts of the assembly call by name: view computations, command handlers and phases."""
	return tuple(view.compute for view in spec.publishes) + tuple(name for _command, name in spec.applies) \
		+ tuple(hook.method for hook in spec.phases) + tuple(provision.method for provision in spec.provides)


