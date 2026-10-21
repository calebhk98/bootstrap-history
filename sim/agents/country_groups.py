"""The interest groups of a country: who is out of pocket in it, what its state has undertaken to make good, and what it pays.

Groups form the way the home country's do, from the sectors of the country's own bodies of people, firms, foundations and
servants (`Sector.of_*`), read at the country's own pay and prices; the same `InterestGroup` actor presses the same
`Government`, scoped to the country. `CountryWorld` mixes this in."""
from typing import Any, Dict, List

from .sector import CONCESSION_PREFIX, Sector, sector_key

# the kinds of actor that are a country's foundations
FOUNDATION_KINDS = ("church", "academy")


class CountryGroupsView:
	"""The group-facing readings of `CountryWorld`; `profile`, `_shared`, `_holder`, `government` and `country_strata` are its."""

	profile: Any
	_holder: Any

	def government(self) -> Any:
		raise NotImplementedError

	def country_strata(self) -> List[Any]:
		raise NotImplementedError

	def _own_economy(self) -> Any:
		raise NotImplementedError

	def _answer(self, figure: str, answer: Any) -> Any:
		raise NotImplementedError

	def _country_actors(self, kinds: Any) -> List[Any]:
		"""The actors of these kinds that answer to the country, still in business, in id order."""
		of_kind = getattr(self._holder, "of_kind", None)
		if of_kind is None:
			return []
		country_of = self._holder.country_of
		return [actor for kind in kinds for actor in of_kind(kind)
				if actor.record.exited_year is None and country_of(actor) == self.profile.country]

	def sectors(self) -> Dict[str, Sector]:
		"""Everyone of the country hurt this year, by key; read once for the year this scope lives. None of the loss is the
		founder's doing that the country can see, so no blame is laid at his door."""
		kept = getattr(self, "_sectors", None)
		if kept is not None:
			return kept
		strata = [stratum for stratum in self.country_strata()]
		firms = self._country_actors(("firm",))
		foundations = self._country_actors(FOUNDATION_KINDS)
		state = self.government()
		falling = (Sector.of_strata(strata, self) + Sector.of_firms(firms, self) + Sector.of_foundations(foundations)
				   + (Sector.of_servants(state, self) if hasattr(state, "record") else []))
		for sector in falling:
			sector.blame_share = 0.0
		Sector.remember_welfare(strata, self)
		Sector.remember_margins(firms)
		Sector.remember_foundations(foundations)
		if hasattr(state, "record"):
			Sector.remember_servants(state, self)
		self._sectors = {sector_key(sector.kind, sector.subject): sector for sector in falling}
		return self._sectors

	def idle_hours_by_trade(self) -> Dict[str, Any]:
		"""(hours offered and not hired, hours offered) of each trade in the country's own labour markets last year."""
		return dict(self._answer("idle hours", self._own_economy().idle_hours_by_trade()))

	def group_claims(self) -> Dict[str, float]:
		"""What the country's state has undertaken to make good to each organised group of the country, by budget line name."""
		return {CONCESSION_PREFIX + group.actor_id: group.record.claim for group in self._country_actors(("interest_group",))
				if group.organised()}

	def faction_backing(self) -> Dict[str, float]:
		"""The weight each organised group of the country can put behind a claimant to the throne: its strength."""
		return {group.actor_id: group.record.strength for group in self._country_actors(("interest_group",))
				if group.organised() and group.record.strength > 0.0}

	def scope_revenue(self, scope: float) -> float:
		"""The state's yearly revenue from a territory holding `scope` of the country."""
		return max(1e-9, self.state_revenue() * scope)  # type: ignore[attr-defined,no-any-return]

	def state_in_deficit(self) -> bool:
		"""Whether the country's state could pay all it set out to last year."""
		record = getattr(self.government(), "record", None)
		return record is not None and sum(record.unfunded.values()) > 1e-9

	def concession_paid(self, line_name: str) -> float:
		"""What the country's state paid last year on a named line of its budget."""
		record = getattr(self.government(), "record", None)
		return 0.0 if record is None else max(0.0, record.need.get(line_name, 0.0) - record.unfunded.get(line_name, 0.0))

	def say(self, text: Any) -> None:
		"""A country's groups report to its own state; the founder's log does not carry them."""
