"""What the parts of a country's world share: answering from the shared world's same part, and the country's own economy."""
from typing import Any, Optional

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
	"""A part of a country's world. What a subclass defines the country answers itself; every other member of the part's
	protocol (sim/agents/protocols.py) is installed when the subclass is created as a call to the shared (home) world's same
	part. `world` is the country's world; `part` names the part."""

	part: str = ""

	def __init_subclass__(cls, **keywords: Any) -> None:
		super().__init_subclass__(**keywords)
		if not cls.part:
			return
		protocol = protocols.World.__annotations__[cls.part]
		protocol = getattr(protocols, protocol) if isinstance(protocol, str) else protocol
		for name, member in vars(protocol).items():
			if name.startswith("_") or hasattr(cls, name):
				continue
			setattr(cls, name, _forwarded_attribute(name) if isinstance(member, property) else _forwarder(name))
		for name in getattr(protocol, "__annotations__", {}):
			if not name.startswith("_") and not hasattr(cls, name):
				setattr(cls, name, _forwarded_attribute(name))

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def shared(self) -> Any:
		"""The shared world's part of this name."""
		return getattr(self.world.shared, self.part)


class SharedDisclosure(SharedPart):
	part = "disclosure"


class SharedSeats(SharedPart):
	part = "seats"


class SharedCapacity(SharedPart):
	part = "capacity"


class SharedTrade(SharedPart):
	part = "trade"


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
