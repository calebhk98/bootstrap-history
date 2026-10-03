"""Containers that report their own mutation, and the active-project record built on them.

Generic: they know nothing of the engine. The engine wraps its cache-keyed collections in them so a
cache keyed off a collection's membership cannot go stale.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


class _InvalidatingSet(set):
    """A set that calls `on_change` after every mutation, with no exceptions.

    Backs `Sim.operating` (see the `operating` property on `EconomyMixin`
    below) so that a cache keyed off operating's exact membership -
    `capability_factor()`'s - cannot go stale, no matter which of the nine
    call sites across core.py/projects.py/economy.py/society.py adds to or
    discards from it, and without asking any of them to remember a second
    line. The `done`/`_done_changed()` convention this project already has
    relies on every one of ITS mutation sites remembering to call
    `_done_changed()` by hand; that is a real convention and it has held,
    but a second one just like it - one more rule written down at every call
    site instead of enforced at one - is exactly the shape that has already
    produced three drifted-apart bugs elsewhere in this codebase today. This
    set makes the equivalent mistake impossible for `operating` specifically:
    there is only one `.add`, only one `.discard`, and they are these. It is
    the same reasoning that made `revealed` (engine/fog.py) a property rather
    than a plain attribute, extended to a set instead of a ratchet.

    Every mutating method a plain `set` exposes is overridden so that
    swapping this in for `set()` changes nothing observable except that
    `on_change` now fires. Non-mutating methods (`copy`, `union`, membership
    tests, iteration, `len`) are inherited unchanged.
    """

    def __init__(self, iterable=(), on_change=None):
        set.__init__(self, iterable)
        self._on_change = on_change

    def _fire(self):
        if self._on_change is not None:
            self._on_change()

    def add(self, item):
        if item not in self:
            set.add(self, item)
            self._fire()

    def discard(self, item):
        if item in self:
            set.discard(self, item)
            self._fire()

    def remove(self, item):
        set.remove(self, item)      # raises KeyError, same as a plain set
        self._fire()

    def pop(self):
        item = set.pop(self)
        self._fire()
        return item

    def clear(self):
        if self:
            set.clear(self)
            self._fire()

    def update(self, *others):
        before = len(self)
        set.update(self, *others)
        if len(self) != before:
            self._fire()

    def difference_update(self, *others):
        before = len(self)
        set.difference_update(self, *others)
        if len(self) != before:
            self._fire()

    def intersection_update(self, *others):
        before = len(self)
        set.intersection_update(self, *others)
        if len(self) != before:
            self._fire()

    def symmetric_difference_update(self, other):
        before = frozenset(self)
        set.symmetric_difference_update(self, other)
        if frozenset(self) != before:
            self._fire()

    def __ior__(self, other):
        before = len(self)
        result = set.__ior__(self, other)
        if len(self) != before:
            self._fire()
        return result

    def __iand__(self, other):
        before = len(self)
        result = set.__iand__(self, other)
        if len(self) != before:
            self._fire()
        return result

    def __isub__(self, other):
        before = len(self)
        result = set.__isub__(self, other)
        if len(self) != before:
            self._fire()
        return result

    def __ixor__(self, other):
        before = frozenset(self)
        result = set.__ixor__(self, other)
        if frozenset(self) != before:
            self._fire()
        return result


class _InvalidatingDict(dict):
    """A dictionary that calls `on_change` after every mutation.

    Follows the exact pattern of _InvalidatingSet above. Used for
    `self.household.active` and `self.household.employees` so that
    derived-state caches keyed on active project membership or workforce
    changes are reliably invalidated whenever keys or values mutate,
    without requiring scattered callers across the engine to remember
    manual cache resets.

    Nested dictionary values (such as project states in active projects and
    their nested lab_left trade requirements) are recursively wrapped so that
    in-place modifications, field updates, and alias mutations automatically
    bubble invalidation up to the root container's on_change listener.
    """

    def __init__(self, *args, on_change=None, **kwargs):
        self._on_change = on_change
        super().__init__()
        if args or kwargs:
            for key, value in dict(*args, **kwargs).items():
                super().__setitem__(key, self._wrap_value(value))

    def _fire(self):
        if self._on_change is not None:
            self._on_change()

    def _wrap_value(self, value):
        if isinstance(value, ActiveProjectState):
            value._on_change = self._fire
            return value
        if isinstance(value, _InvalidatingDict):
            value._on_change = self._fire
            return value
        if isinstance(value, dict):
            if "ph_left" in value:
                return ActiveProjectState.from_dict(value, _on_change=self._fire)
            return _InvalidatingDict(value, on_change=self._fire)
        return value

    def __setitem__(self, key, value):
        super().__setitem__(key, self._wrap_value(value))
        self._fire()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._fire()

    def pop(self, *args, **kwargs):
        result = super().pop(*args, **kwargs)
        self._fire()
        return result

    def popitem(self):
        result = super().popitem()
        self._fire()
        return result

    def clear(self):
        if self:
            super().clear()
            self._fire()

    def update(self, *args, **kwargs):
        other_items = dict(*args, **kwargs)
        if not other_items:
            return
        for key, value in other_items.items():
            super().__setitem__(key, self._wrap_value(value))
        self._fire()

    def setdefault(self, key, default=None):
        if key not in self:
            wrapped = self._wrap_value(default)
            result = super().setdefault(key, wrapped)
            self._fire()
            return result
        return super().__getitem__(key)

    def __ior__(self, other):
        self.update(other)
        return self


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
	status: str = "ACTIVE"

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
		status: str = "ACTIVE",
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
		super().__setitem__("status", status)
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
