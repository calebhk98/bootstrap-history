"""A published view at run time: computes through its owner, caches under its signature, applies mod adjusters."""
from typing import Any, Callable, Dict, List, Optional, Tuple

from .clock import Clock
from .errors import StaleView
from .spec import KEYED, QUOTE, ViewSpec


class View:
	"""`view()` for a table or a quote with arguments, `view[key]` for a keyed view."""

	def __init__(self, spec: ViewSpec, owner_id: str, compute: Callable, clock: Clock):
		self.spec = spec
		self.owner_id = owner_id
		self.compute = compute
		self.clock = clock
		self.inputs: List["View"] = []
		self.adjusters: List[Tuple[Callable, Any, List["View"]]] = []   # (function, its needs, the views it reads)
		self.entries: Dict[Optional[str], Tuple[tuple, Any]] = {}      # acting seat -> (signature, value or keyed dict)
		self.memo_epoch = -1
		self.memo_signature: tuple = ()
		self.hits = 0

	def signature(self) -> tuple:
		clock = self.clock
		if self.memo_epoch == clock.epoch:
			return self.memo_signature
		seat_scoped = self.spec.seat_scoped
		parts: List[Any] = [clock.era, clock.acting_seat if seat_scoped else None]
		parts.extend(clock.counter(self.owner_id, channel, seat_scoped) for channel in self.spec.channels)
		parts.extend(view.signature() for view in self.inputs)
		for _function, _needs, reads in self.adjusters:
			parts.extend(view.signature() for view in reads)
		self.memo_signature = tuple(parts)
		self.memo_epoch = clock.epoch
		return self.memo_signature

	def fresh(self, *arguments: Any, **keywords: Any) -> Any:
		value = self.compute(*arguments, **keywords)
		for function, needs, _reads in self.adjusters:
			value = function(needs, value, *arguments, **keywords)
		return value

	def __call__(self, *arguments: Any, **keywords: Any) -> Any:
		kind = self.spec.kind
		if kind == KEYED:
			raise TypeError("view %s is keyed: read it as view[key]" % self.spec.name)
		if kind == QUOTE or not self.spec.cached:
			return self.fresh(*arguments, **keywords)
		if arguments or keywords:
			raise TypeError("view %s is a table and takes no arguments" % self.spec.name)
		signature = self.signature()
		seat = self.clock.acting_seat if self.spec.seat_scoped else None
		entry = self.entries.get(seat)
		if entry is not None and entry[0] == signature:
			self.check_shadow(entry[1])
			return entry[1]
		value = self.fresh()
		self.entries[seat] = (signature, value)
		return value

	def __getitem__(self, key: Any) -> Any:
		if self.spec.kind != KEYED:
			raise TypeError("view %s is not keyed: read it as view()" % self.spec.name)
		if not self.spec.cached:
			return self.fresh(key)
		signature = self.signature()
		seat = self.clock.acting_seat if self.spec.seat_scoped else None
		entry = self.entries.get(seat)
		if entry is None or entry[0] != signature:
			entry = (signature, {})
			self.entries[seat] = entry
		values = entry[1]
		if key in values:
			self.check_shadow(values[key], key)
			return values[key]
		value = values[key] = self.fresh(key)
		return value

	def check_shadow(self, cached: Any, *arguments: Any) -> None:
		every = self.clock.shadow_every
		if not every:
			return
		self.hits += 1
		if self.hits % every == 0 and self.fresh(*arguments) != cached:
			raise StaleView("view %s of module %s served a cached value that a fresh computation contradicts%s" % (
				self.spec.name, self.owner_id, " (key %r)" % (arguments[0],) if arguments else ""))


