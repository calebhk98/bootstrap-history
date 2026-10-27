"""One-line forwarders from the old `Sim` names of production to the production module, for callers not yet in a module.

The screens, the project phases, the agent economy's port, the labour core and the tests still say `sim.running(node)`, `sim.revenue()` or
`sim.industry_depth(node)`; each line goes when its last caller reads the view or sends the command itself."""
from sim.markets.api import ResetMarketCaches
from sim.materials.api import ForgetReadings
from sim.production.api import AccrueExperience, LearnFromFailure, caches, constants

from sim.invalidating import _InvalidatingDict

from . import money_units, node_rederive, society_holdings
from .readable import readable


class ForwardProductionMixin:

	# the numbers other topics' code, the screens and the tests still read off the game (sim/production/constants.py declares them)
	vars().update({name: value for name, value in vars(constants).items() if name.isupper()})
	REVENUE_CEILING_PER_POP_SCALE = money_units.PricedInLabourHours("REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE")
	CAPABILITY_FACTOR_HALF_SATURATION_REV = money_units.PricedInLabourHours("CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS")
	INSTITUTION_PLACES_FALLBACK_UPKEEP_PER_HEAD = money_units.PricedInLabourHours(
		"INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD")

	# ---- what is running ----

	def running(self, node_id):
		return self.view("running")[node_id]

	def is_venture(self, node_id):
		return self.view("is_venture")[node_id]

	def is_concern_node(self, node_id):
		return self.view("is_concern_node")[node_id]

	def capability_gaps(self):
		return self.view("capability_gaps")()

	def institution_units(self, node_id):
		return self.view("institution_units")[node_id]

	def institution_unit_ceiling(self, node_id):
		return self.view("institution_unit_ceiling")[node_id]

	def institution_unit_cost(self, node_id, have_units, add_units):
		return self.view("institution_unit_cost")(node_id, have_units, add_units)

	# ---- revenue and upkeep ----

	@readable
	def revenue(self):
		return self.view("revenue_estimate")()

	def revenue_capacity(self):
		return self.view("revenue_capacity")()

	def estimated_revenue(self):
		return self.view("estimated_revenue")()

	def concern_revenue(self, node_id):
		return self.view("concern_revenue")[node_id]

	@readable
	def revenue_sources(self):
		return self.view("revenue_sources")()

	def founder_wage_income(self):
		return self.view("founder_wage_income")()

	def workshop_output(self):
		return self.view("workshop_output")()

	def capability_factor(self):
		return self.view("capability_factor")()

	def ledger_concern_rows(self):
		return self.view("concern_market")()

	def held_trade(self):
		return self.view("held_trade")()

	def still_ramping(self):
		return self.view("still_ramping")()

	def venture_ramp(self, node_id):
		return self.view("venture_ramp")[node_id]

	@readable
	def upkeep(self):
		return self.view("upkeep")()

	@readable
	def upkeep_by_concern(self):
		return self.view("upkeep_by_concern")()

	def institution_upkeep(self, node_id, units=None, fully_staffed=False):
		return self.view("institution_upkeep")(node_id, units, fully_staffed)

	def institution_places(self, node_id):
		return self.view("institution_places")[node_id]

	def _practice_set(self):
		return self.view("practice_set")()

	def _practisable(self, node_id):
		return self.view("practisable")[node_id]

	# ---- what a concern sells and takes ----

	def concern_goods_have_market(self, node_id):
		return self.view("concern_goods_have_market")[node_id]

	def node_output_market_factor(self, node, selling_seat=None):
		return self.view("node_output_market_factor")(node, selling_seat)

	def concern_sale_basis(self, node_id):
		return self.view("concern_sale_basis")[node_id]

	def concern_takings(self, node_id, ramp, with_output_factor=True, cost_scale=None):
		return self.view("concern_takings")(node_id, ramp, with_output_factor=with_output_factor, cost_scale=cost_scale)

	def concern_book_offer(self, node_id):
		return self.view("concern_book_offer")[node_id]

	def concern_book_inputs_cost(self, node_id):
		return self.view("concern_book_inputs_cost")[node_id]

	def concern_volume_ratio(self, node_id):
		return self.view("concern_volume_ratio")(node_id)

	def concern_value_ratio(self, node_id):
		return self.view("concern_value_ratio")[node_id]

	def concern_learning_ratio(self, node_id):
		return self.view("concern_learning_ratio")[node_id]

	def concern_baskets_now(self, node_id):
		return self.view("concern_baskets_now")[node_id]

	# ---- industry experience ----

	def industry_depth(self, node_id):
		return self.view("industry_depth")[node_id]

	def industry_scale_ceiling(self, node_id):
		return self.view("industry_scale_ceiling")[node_id]

	def industry_experience(self, node_id):
		return self.view("industry_experience")[node_id]

	def founding_worker_years(self, node_id):
		return self.view("founding_worker_years")[node_id]

	def concern_runs_without_founder(self, node_id):
		return self.view("concern_runs_without_founder")[node_id]

	def learn_from_failed_attempt(self, node_id):
		self.send(LearnFromFailure(node_id))

	def after_failed_attempts(self, node_id, count):
		return self.view("failed_attempts_trial")(node_id, count)

	def accrue_industry_experience(self):
		self.send(AccrueExperience())

	# ---- the techniques in use ----

	def techniques_in_use(self):
		return self.view("techniques_in_use")()

	def techniques_epoch(self):
		return self.view("techniques_epoch")()

	def price_epoch(self):
		return self.view("price_epoch")()

	# ---- the memos over what is done and operating ----
	# Plain calls on the household, not commands: the household's hooks fire while a game is still being built, before any module exists.

	def done_in_order(self):
		return self.view("done_in_order")()

	def _done_changed(self):
		"""Call after anything adds to or removes from the set of techniques done (or granted)."""
		caches.forget_done(self.household)

	def _operating_changed(self):
		"""Call after anything adds to or removes from what is operating."""
		caches.forget_operating(self.household)

	def _active_changed(self):
		"""Call after anything adds to, removes from, or updates the projects in hand."""
		caches.forget_active(self.household)

	def _reset_operating(self):
		"""Point the seat's business at the invalidation hook and invalidate once."""
		self.state.projects.business.watch = self._operating_changed
		self._operating_changed()

	def _reset_active(self):
		"""Re-wrap the projects in hand in a fresh invalidating dict and invalidate once."""
		self.state.projects.active = _InvalidatingDict(self.state.projects.active or {}, on_change=self._active_changed)
		self._active_changed()

	def _reset_economic_caches(self):
		"""Wipe all transient economic derived-state caches and re-wrap containers on save/load and on a seat switch."""
		caches.forget_revenue(self.household)
		self.send(ResetMarketCaches())      # the markets module's remembered goods-category figures
		self.send(ForgetReadings())      # the materials module's remembered demand tables
		self._done_changed()
		self._reset_operating()
		self._reset_active()
		self._reset_workforce()

	# ---- the tree's derived figures (composition: node_rederive.py) ----

	def refresh_derived_nodes(self):
		node_rederive.refresh_derived_nodes(self)

	def _remember_derived_gates(self, held_techs):
		node_rederive.remember_derived_gates(self, held_techs)

	def _society_held_techs(self):
		return society_holdings.society_techs(self)
