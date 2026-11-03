"""What a country's state is asked to give the clients of its own (the seats that play in the country and run the funding
mechanic), at the country's own pay, reach, size and real output per head."""
from . import patronage
from .country_part import SharedPart


class CountryPatronage(SharedPart):
	"""The patronage reading of `CountryWorld`."""

	part = "patronage"

	def patron_ask(self) -> float:
		"""What the country's state is asked for in direct funding: nothing while no seat of the country runs the mechanic;
		else each client's ask at the country's pay for an hour of work, real output per head and reach. Refuses
		(NoCountryEconomy) where the economy has no pay or output for the country."""
		world = self.world
		profile = world.profile
		clients = self.shared.patron_clients(profile.country)
		if not clients:
			return 0.0
		people = world.people.population_total()
		unskilled = world.shared.labour.trade_of_role("unskilled")
		hour_money = world.own.answer("unskilled pay", world.own.get().pay_per_person_year(unskilled)) / world.shared.labour.hours_per_person_year
		per_head = world.own.answer("real output per head", self.shared.country_output_per_head(profile.country, profile.population, people))
		return patronage.ask_of_country(self.shared.state_funding_terms(people), hour_money, per_head, world.taxpayers.state_reach(), clients)  # type: ignore[no-any-return]
