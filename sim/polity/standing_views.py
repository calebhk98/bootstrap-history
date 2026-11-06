"""The polity module's value weights and the views of one seat's figures."""

from sim.assembly.api import Part


class StandingViews(Part):

	def value_weights(self):
		"""The society's value weights, by name."""
		return self.world.value_weights

	def standing(self):
		"""The acting seat's figures with its society and state."""
		seat = self.seat
		return {"protection": seat.protection, "scandal": seat.scandal, "bribes_year_to_date": seat.bribes_ytd,
		        "reputation": seat.reputation, "scandal_last_year": seat.scandal_last_year, "eminence": seat.eminence,
		        "familiarity": seat.familiarity, "demand_stance": seat.demand_stance, "service_offer": seat.service_offer,
		        "concealed": seat.concealed, "defiance": seat.defiance, "last_withdrawal": seat.last_withdrawal,
		        "governance": seat.gov}

	def eminence(self):
		return self.seat.eminence

	def value_weight(self, key):
		return self.world.value_weights[key]
