"""What the parts of a country's world share: answering from the shared world's same part, and the country's own economy."""
from typing import Any, FrozenSet, Optional

from . import protocols
from .no_country_economy import NoCountryEconomy


def _forwarder(name: str) -> Any:
	def forward(self: Any, *arguments: Any, **keywords: Any) -> Any:
		return getattr(self.shared, name)(*arguments, **keywords)
	forward.__name__ = name
	return forward


def _forwarded_attribute(name: str) -> property:
	return property(lambda self: getattr(self.shared, name))


class SharedPart:
	"""A part of a country's world. Every member of the part's protocol (sim/agents/protocols.py) is either defined by the
	subclass, so the country answers it itself, or named in its `home_members`, answered by the shared (home) world's same
	part because the figure is the same for every country. A member that is neither is an error when the subclass is
	created. `world` is the country's world; `part` names the part."""

	part: str = ""
	home_members: FrozenSet[str] = frozenset()

	def __init_subclass__(cls, **keywords: Any) -> None:
		super().__init_subclass__(**keywords)
		if not cls.part:
			return
		protocol = protocols.World.__annotations__[cls.part]
		protocol = getattr(protocols, protocol) if isinstance(protocol, str) else protocol
		members = {name: member for name, member in vars(protocol).items() if not name.startswith("_")}
		members.update({name: None for name in getattr(protocol, "__annotations__", {}) if not name.startswith("_")})
		members = {name: member for name, member in members.items() if name not in ("part", "home_members")}
		unknown = cls.home_members - set(members)
		defined = {name for name in cls.home_members if name in vars(cls)}
		unanswered = sorted(name for name in members if name not in cls.home_members and not hasattr(cls, name))
		if unknown or defined or unanswered:
			raise TypeError("%s: home_members not in the protocol %s; home_members also defined %s; protocol members neither "
							"defined nor in home_members %s" % (cls.__name__, sorted(unknown), sorted(defined), unanswered))
		for name in cls.home_members:
			member = members[name]
			setattr(cls, name, _forwarder(name) if callable(member) and not isinstance(member, property) else _forwarded_attribute(name))

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def shared(self) -> Any:
		"""The shared world's part of this name."""
		return getattr(self.world.shared, self.part)


class SharedDisclosure(SharedPart):
	part = "disclosure"
	# home: how a technique's secret is kept and patented is the shared world's rule, the same for every country
	home_members = frozenset(("base_visibility", "collect_royalty", "disclosure_mode", "patent_entry", "proof_years", "secret_exposure", "state_grants_patents"))


class SharedSeats(SharedPart):
	part = "seats"
	# home: seats are the players', not a country's: every actor reads the same seats
	home_members = frozenset(("founder_review", "release_seat_staff", "seat_margin", "seat_parties"))


class SharedCapacity(SharedPart):
	part = "capacity"
	# home: a plant's cost and span come from the technique and the shared market, not from the country
	home_members = frozenset(("expansion_gain", "plant_cost", "running_cost", "span_factor"))


class SharedTrade(SharedPart):
	part = "trade"
	# home: places, freight and markets are one map for every country
	home_members = frozenset(("country_of_place", "delivered_this_year", "freight_between", "has_market", "market_depth", "price_after_cargo", "price_at", "ship", "trade_materials", "trade_places"))


class OwnEconomy:
	"""The agent economy's answers for one country, read through the shared world."""

	def __init__(self, shared_world: Any, profile: Any) -> None:
		self.shared_world = shared_world
		self.profile = profile

	def get(self) -> Any:
		"""The economy's answers for this country; raises NoCountryEconomy when it has none."""
		lookup = getattr(getattr(self.shared_world, "people", None), "country_economy", None)
		own = lookup(self.profile.country) if callable(lookup) else None
		if own is None:
			raise NoCountryEconomy(self.profile.country)
		return own

	def get_or_none(self) -> Optional[Any]:
		try:
			return self.get()
		except NoCountryEconomy:
			return None

	def answer(self, figure: str, answer: Any) -> Any:
		"""`answer`, or a refusal naming the figure where the economy has none."""
		if answer is None or answer == {}:
			raise NoCountryEconomy(self.profile.country, figure)
		return answer
