"""What a patron state funds: the founder's ask, the clients a state is asked to fund, and what the treasury has paid.

Needs: running_mechanics, real_output_per_head, state_reach, pop_scale, rep_factor, money_per_labour_hour, civilisation,
seat_list, seat_country, acting_as, government_figures, acting_seat."""
from sim.agents.api import patronage
from sim.seats.api import patron_grant_share

from . import constants


class Patronage:

	def patron_funding_ask(self):
		"""What a patron state would give the founder in a year if its treasury could spare it."""
		needs = self.needs
		if not needs.running_mechanics("state_funding"):
			return 0.0
		return patronage.ask(self.priced(constants.STATE_FUNDING_BASE_LABOUR_HOURS), needs.real_output_per_head(),
		                     self.state_reach(), needs.pop_scale(), constants.STATE_FUNDING_POP_SCALE_EXPONENT, self.seat.gov,
		                     constants.STATE_FUNDING_GOV_QUALITY_SCALE, needs.rep_factor())

	def state_funding_terms(self):
		"""The figures a state funds a client on: the labour hours of its base sum, the exponent of the country's size and the
		scale of the client's governance."""
		return {"base_hours": constants.STATE_FUNDING_BASE_LABOUR_HOURS, "exponent": constants.STATE_FUNDING_POP_SCALE_EXPONENT,
		        "governance_scale": constants.STATE_FUNDING_GOV_QUALITY_SCALE}

	def patron_clients(self, country):
		"""(seat id, governance, reputation factor) of the playing seats of `country` whose techniques run the `state_funding`
		mechanic: the clients its state is asked to fund (a seat with no country is the home country's)."""
		needs = self.needs
		home = str(needs.civilisation().get("id"))
		clients = []
		for seat_id in needs.seat_list()["playing"]:
			if (needs.seat_country[seat_id] or home) != country:
				continue
			with needs.acting_as(seat_id):
				if needs.running_mechanics("state_funding"):
					clients.append((seat_id, max(0.0, self.seat.gov), needs.rep_factor()))
		return clients

	def state_funding(self):
		"""What the treasury has paid the founder this year; the government decides it from its purse after its standing need.
		A seat of another country is paid by that country's state, its grant shared among the seats that state funds."""
		needs = self.needs
		return patron_grant_share(self.patron_grant_of, needs.seat_country[needs.acting_seat()], needs.acting_seat(),
		                          str(needs.civilisation().get("id")), self.patron_clients)

	def patron_grant_of(self, country):
		"""What the state of `country` pays its clients this year, or None when it has no record."""
		figures = self.needs.government_figures[country]
		return None if figures is None else figures[0]
