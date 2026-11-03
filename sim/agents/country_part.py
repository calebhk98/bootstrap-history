"""What the parts of a country's world share: answering from the shared world's same part, and the country's own economy."""
from typing import Any, Optional

from .no_country_economy import NoCountryEconomy


class SharedPart:
	"""A part of a country's world. What a subclass defines the country answers itself; any other member of its protocol is
	the shared (home) world's same part, asked as it is. `world` is the country's world; `part` names the part."""

	part: str = ""

	def __init__(self, world: Any, part: Optional[str] = None) -> None:
		self.world = world
		if part is not None:
			self.part = part

	@property
	def shared(self) -> Any:
		"""The shared world's part of this name."""
		return getattr(self.world.shared, self.part)

	def __getattr__(self, name: str) -> Any:
		# only reached for a name this class does not define; the guard keeps a copy or a load from recursing
		if name.startswith("__") or name in ("world", "part", "shared"):
			raise AttributeError(name)
		return getattr(self.shared, name)


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
