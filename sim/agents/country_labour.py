"""What a country's actors see of its labour markets: pay, people of a trade, who is free to hire, and paying wages out."""
from typing import Any, Optional

from . import ledger
from .country_part import SharedPart
from .country_state_crew import people_left
from .edges import EDGE_WORKERS
from .payroll import share_out


class CountryLabour(SharedPart):
	"""The country's own labour markets, read through its part of the economy."""

	part = "labour"
	# home: trade names and the hours in a person-year are the same in every country
	home_members = frozenset(("hours_per_person_year", "labour_market", "trade_exists", "trade_of_role"))

	def pay_per_person_year(self, trade: str) -> float:
		"""What a person-year of a trade pays in this country's own labour markets."""
		return self.world.own.get().pay_per_person_year(trade)

	def hourly_pay(self, trade: str) -> float:
		"""What an hour of a trade pays in this country's own labour markets."""
		return self.pay_per_person_year(trade) / self.shared.hours_per_person_year

	def national_people(self, trade: str) -> float:
		"""People of a trade in the country: those its labour markets hold in the trade; for unskilled labour, every
		working person its labour markets hold (the working age, as at home). Refuses (NoCountryEconomy) where the
		economy has no part for the country or its labour markets hold nobody; never the profile's working age."""
		own = self.world.own
		economy = own.get()
		if trade == self.shared.trade_of_role("unskilled"):
			return float(own.answer("working people", economy.working_people()))
		return float(economy.people_of_trade(trade))

	def free_fte(self, trade: str, actor_id: Optional[str]) -> Optional[float]:
		"""People of a trade left in this country's labour markets for `actor_id`; None when the economy has no part for the
		country, never the founder's pool."""
		economy = self.world.own.get_or_none()
		if economy is None:
			return None
		count = self.world.holder.staff.staff_fte_in_country(trade, self.world.profile.country, actor_id)
		return people_left(economy.people_of_trade(trade), count)

	def pay_wages(self, payer: Any, amount: float, purpose: Any) -> None:
		"""Pay a country's people: its free strata by their numbers, or the workers' edge while it has none."""
		people = [stratum for stratum in self.world.people.country_strata()
			  if stratum.record.exited_year is None and not stratum.is_bonded() and stratum.record.members > 0.0]
		if not people:
			ledger.transfer(payer, self.world.setting.edge(EDGE_WORKERS), amount, purpose)
			return
		share_out(payer, people, [stratum.record.members for stratum in people], amount, purpose)
