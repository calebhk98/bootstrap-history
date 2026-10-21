"""What a country's state is asked to give the clients of its own (the seats that play in the country and run the funding
mechanic), at the country's own pay, reach, size and real output per head. `CountryWorld` mixes this in."""
from typing import Any

from . import patronage
from .country_state import UNSKILLED_TRADE


class CountryPatronageView:
	"""The patronage reading of `CountryWorld`; `profile`, `_shared`, `_own_economy` and `_answer` are its."""

	profile: Any
	_shared: Any

	def _own_economy(self) -> Any:
		raise NotImplementedError

	def _answer(self, figure: str, answer: Any) -> Any:
		raise NotImplementedError

	def patron_ask(self) -> float:
		"""What the country's state is asked for in direct funding: nothing while no seat of the country runs the mechanic;
		else each client's ask at the country's pay for an hour of work, real output per head and reach. Refuses
		(NoCountryEconomy) where the economy has no pay or output for the country."""
		clients = self._shared.patron_clients(self.profile.country)
		if not clients:
			return 0.0
		people = self.population_total()  # type: ignore[attr-defined]
		hour_money = self._answer("unskilled pay", self._own_economy().pay_per_person_year(UNSKILLED_TRADE)) / self._shared.hours_per_person_year
		per_head = self._answer("real output per head", self._shared.country_output_per_head(self.profile.country, self.profile.population, people))
		return patronage.ask_of_country(self._shared.state_funding_terms(people), hour_money, per_head, self.state_reach(), clients)  # type: ignore[attr-defined,no-any-return]
