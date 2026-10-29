"""What a concern costs to open and reopen, and what it really earns and costs: one figure for every screen."""
from sim.agents.api import business_books
from sim.production.api import concern_earnings
from sim.projects.api import closure_grace, constants as project_constants

from . import constants, rules


class Quotes:
	def venture_capex(self, node_id):
		"""What it costs to open the doors, over and above having worked out how. Stock, premises, the first year's
		materials: a fraction of what the work itself cost, and never less than a year of its running cost, so that a thing
		which is cheap to invent and expensive to run cannot be opened for nothing."""
		node = self.needs.tree_nodes()[node_id]
		return max(self.needs.project_cost(node_id) * constants.VENTURE_CAPEX_SHARE_OF_BUILD_COST,
		           node["up"] * constants.VENTURE_CAPEX_MIN_UPKEEP_YEARS)

	def opening_fee(self, node_id, units=None):
		"""(charge, size) for opening a concern now; `open` charges exactly this.

		A starter founding of a scalable institution has a floor on its size; reopening restores the prior size, not a full
		founding."""
		if node_id in self.needs.capability_sets()[1] and units is not None:
			unit_count = max(project_constants.STARTER_FOUNDING_MIN_UNITS, float(units))
		else:
			unit_count = self.reopen_units(node_id)
		return self.reopen_fee(node_id, unit_count), unit_count

	def reopen_units(self, node_id):
		"""How much of a scalable institution a reopening restores (one, for anything else)."""
		if node_id not in self.needs.capability_sets()[1]:
			return 1.0
		return self.needs.legacy_projects().business.size_of(node_id)

	def reopen_fee(self, node_id, unit_count=1.0):
		"""What bringing a shut concern back costs, for `open` and `restore` alike.

		A concern the staffing rule shut within STAFF_CLOSURE_GRACE keeps its premises, so it costs a fraction; any other shut
		concern costs the ordinary opening fee. A work that is not a concern costs a share of building it again, never less
		than some years of its upkeep."""
		needs = self.needs
		if needs.is_venture[node_id]:
			fee = self.venture_capex(node_id) * unit_count
		else:
			fee = max(needs.project_cost(node_id) * project_constants.RESTORE_COST_SHARE_OF_BUILD,
			          needs.tree_nodes()[node_id]["up"] * project_constants.RESTORE_COST_MIN_UPKEEP_YEARS)
		return closure_grace.fee_after_grace(fee, needs.staff_closure_age[node_id], project_constants.STAFF_CLOSURE_GRACE,
		                                     project_constants.STAFF_CLOSURE_DISCOUNT)

	def reopen_fee_at_prior_size(self, node_id):
		"""What reopening costs at the size the plant had (the view other modules read as `reopen_fee`)."""
		return self.reopen_fee(node_id, self.reopen_units(node_id))

	def venture_real_earnings(self, node_id, units=None, fully_ramped=False, with_output_factor=True):
		"""Yearly takings as the ledger credits them, the figure the screens quote and `revenue` sums.

		Applies the price level and the goods market the tree's raw revenue lacks, and, for a running concern, its revenue
		ramp and, if scalable, its units; a concern not yet open is quoted at its full ramp and one unit unless `units` says
		otherwise. `fully_ramped` leaves the ramp out (what it reaches). `with_output_factor` False leaves out the hazard and
		war factor, which `revenue` applies to its total."""
		needs = self.needs
		running = node_id in self.operating()
		ramp = concern_earnings.quoted_ramp(running, fully_ramped, lambda: needs.venture_ramp[node_id])
		units = concern_earnings.quoted_units(running, node_id in needs.capability_sets()[1], lambda: needs.institution_units[node_id], units)
		market = needs.node_output_market_factor(needs.tree_nodes()[node_id], self.clock.acting_seat)
		return business_books.takings_of_size(needs.concern_takings(node_id, ramp, with_output_factor), units, market)

	def venture_forecast_basis(self, node_id):
		"""What the quote of a concern's earnings stands on: `market` (the economy prices its goods) or
		`long_run_no_market_yet` (nobody has sold them, so the quote is at long-run cost and the price they fetch once sold may
		differ a great deal)."""
		return concern_earnings.forecast_basis(self.needs.concern_goods_have_market[node_id])

	def venture_sale_basis(self, node_id):
		"""How much of the output the quote counts as sold: what the seat's last clearing sold, what the market's buyers took
		last year, or all of it at long-run cost where nobody trades the goods (`concern_sales`)."""
		return self.needs.concern_sale_basis[node_id]

	def venture_upkeep_quote(self, node_id, units=None):
		"""Yearly running cost at the current price level, the one source every screen quotes: `now` at today's staffing (what
		the ledger charges) and `at_full_staffing` with every place filled. The two are equal for an ordinary concern. `units`
		prices a stated size of a scalable institution."""
		needs = self.needs
		return rules.upkeep_quote(needs.institution_upkeep(node_id, units), needs.institution_upkeep(node_id, units, fully_staffed=True),
		                          needs.price_index())

	def venture_real_upkeep(self, node_id, units=None):
		"""Yearly running cost at today's staffing: the figure the ledger charges (`upkeep`)."""
		return self.venture_upkeep_quote(node_id, units)["now"]
