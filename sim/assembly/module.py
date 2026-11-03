"""The base every module implementation derives from: its id, what it was handed, and how it says its state changed."""
from types import SimpleNamespace
from typing import Any, Callable, Dict, Optional

from .clock import Clock


class Part:
	"""One piece of a module's behaviour, built by `Module.build_parts` from the module's `PARTS`. It owns the state it keeps
	between calls (set in `__init__`), reads the module's slots, views and clock through the same names
	the module uses, and reaches a sibling part as `self.parts.<name>`, never through the module class. `setup()` runs once after
	every part exists."""

	def __init__(self, module: "Module"):
		self.module = module
		self.parts = module.parts
		self.needs = None                       # set when the assembly wires the module, before any `setup()`
		self.clock = module.clock
		self.module_id = module.module_id
		self.kernels = module.kernels

	@property
	def world(self) -> Any:
		return self.module.world

	@property
	def seat(self) -> Any:
		return self.module.seat

	def setup(self) -> None:
		"""Called once after assembly, with every sibling built; override to build what the part keeps between calls (never saved)."""

	def seat_bound(self) -> None:
		"""As `Module.seat_bound`, for what this part remembers about the acting seat."""

	def kernel(self, name: str) -> Callable:
		return self.kernels[name]

	def seat_of(self, seat_id: str) -> Any:
		return self.module.seat_of(seat_id)

	def act_as(self, seat_id: str):
		return self.needs.act_as(seat_id)

	def bump(self, channel: str) -> None:
		self.clock.bump(self.module_id, channel)

	def bump_seat(self, channel: str, seat_id: Optional[str] = None) -> None:
		self.clock.bump_seat(self.module_id, channel, seat_id)

	def seat_version(self, channel: str) -> tuple:
		return self.module.seat_version(channel)


class Module:
	"""Set up by the assembly before `setup()` runs: `module_id`, `needs` (the views, points and `send` it declared),
	`clock`, and `world` / `seat` (its own saved state, rebound on a load and on every seat switch)."""
	module_id: str
	needs: Any
	clock: Clock
	world: Any = None
	seat: Any = None
	kernels: Dict[str, Callable]                           # this module's kernels by name, as bound by the assembly
	seat_slot_of: Optional[Callable[[str], Any]] = None   # set by the engine: another seat's state, by seat id
	PARTS: Dict[str, type] = {}                            # name -> Part class: the behaviour; the assembly binds a declared method name to the one part that has it
	parts: Any = None                                      # the built parts by name, as attributes (`self.parts.<name>`)

	def build_parts(self) -> None:
		"""Build every part of `PARTS`; the assembly calls this once the module has its id, clock and kernels."""
		self.parts = SimpleNamespace()
		for name, part_class in self.PARTS.items():
			setattr(self.parts, name, part_class(self))

	def wire(self, needs: Any) -> None:
		"""Hand the module, and each of its parts, the views, points and commands it declared."""
		self.needs = needs
		for part in vars(self.parts).values():
			part.needs = needs

	def setup_parts(self) -> None:
		for part in vars(self.parts).values():
			part.setup()

	def kernel(self, name: str) -> Callable:
		"""The function to call for the kernel `name` this module declared: a mod's replacement, else the reference."""
		return self.kernels[name]

	def seat_of(self, seat_id: str) -> Any:
		"""This module's state for the seat `seat_id`, which need not be the acting one (a command that names a seat)."""
		return self.seat_slot_of(seat_id)

	def setup(self) -> None:
		"""Called once after assembly; override to build what the module keeps between calls (never saved)."""

	def seat_bound(self) -> None:
		"""Called after the modules are pointed at another acting seat (and after a load): override to forget what the module
		remembers about the acting seat (a cache, a wrapped container). The default tells each part."""
		for part in vars(self.parts).values() if self.parts is not None else ():
			part.seat_bound()

	def act_as(self, seat_id: str):
		"""A context in which `seat_id` is the acting seat; the seat that was acting returns on leaving it (the assembly answers)."""
		return self.needs.act_as(seat_id)

	def bump(self, channel: str) -> None:
		self.clock.bump(self.module_id, channel)

	def bump_seat(self, channel: str, seat_id: Optional[str] = None) -> None:
		self.clock.bump_seat(self.module_id, channel, seat_id)

	def seat_version(self, channel: str) -> tuple:
		"""What a memo over the acting seat's `channel` is keyed by: it moves with every bump of the channel for this seat and
		on a load, and differs between seats."""
		return (self.clock.era, self.clock.acting_seat) + self.clock.counter(self.module_id, channel, True)
