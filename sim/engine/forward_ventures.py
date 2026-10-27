"""One-line forwarders from the old `Sim` names of the ventures topic to the ventures module, for callers not yet in a module.

The screens, the agent economy's production port and the tests still say `sim.venture_real_earnings(node)`, `sim.open_venture(node)` or
`sim.sell_concern(node)`; each line goes when its last caller reads the view (`sim.view(name)`) or sends the command itself."""
from sim.ventures.api import OpenVenture, RollOut, SellConcern, constants


class VenturesForwardsMixin:

	# the numbers the tests still read off the game (sim/ventures/constants.py declares them)
	vars().update({name: value for name, value in vars(constants).items() if name.isupper()})

	# ---- what a concern ties up ----

	def venture_hands(self, node_id):
		return self.view("venture_hands")[node_id]

	def venture_hands_founder_staffed(self, node_id):
		return self.view("venture_hands_founder_staffed")[node_id]

	def venture_foreman(self, node_id):
		return self.view("venture_foreman")[node_id]

	def venture_foreman_free(self, trade, excluding=None):
		return self.view("venture_foreman_free")(trade, excluding)

	def venture_staff_used(self):
		return self.view("venture_staff_used")()

	def venture_staff_free(self):
		return self.view("venture_staff_free")()

	def venture_staff_who_is_watching_what(self):
		return self.view("venture_staff_who_is_watching_what")()

	# ---- what opening costs and what a concern earns ----

	def venture_capex(self, node_id):
		return self.view("venture_capex")[node_id]

	def opening_fee(self, node_id, units=None):
		return self.view("opening_fee")(node_id, units)

	def venture_real_earnings(self, node_id, units=None, fully_ramped=False, with_output_factor=True):
		return self.view("venture_real_earnings")(node_id, units, fully_ramped, with_output_factor)

	def venture_real_upkeep(self, node_id, units=None):
		return self.view("venture_real_upkeep")(node_id, units)

	def venture_upkeep_quote(self, node_id, units=None):
		return self.view("venture_upkeep_quote")(node_id, units)

	def venture_forecast_basis(self, node_id):
		return self.view("venture_forecast_basis")[node_id]

	def venture_sale_basis(self, node_id):
		return self.view("venture_sale_basis")[node_id]

	# ---- opening, selling, rolling out ----

	def open_venture(self, node_id, units=None):
		return self.send(OpenVenture(node_id, units))

	def quote_concern_sale(self, node_id):
		return self.view("concern_sale_quote")(node_id)

	def sell_concern(self, node_id):
		return self.send(SellConcern(node_id))

	def coverage_nodes(self):
		return self.view("coverage")()

	def coverage_share(self, node_id):
		return self.view("coverage_share")[node_id]

	def coverage_row(self, node_id):
		return self.view("coverage_row")[node_id]

	def units_for_coverage(self, node_id, share):
		return self.view("units_for_coverage")(node_id, share)

	def roll_out(self, node_id, share):
		return self.send(RollOut(node_id, share))
