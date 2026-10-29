"""One-line forwarders from the old `Sim` names of production to the production module, for callers not yet in a module.

The screens, the project phases, the agent economy's port, the labour core and the tests still say `sim.running(node)`, `sim.revenue()` or
`sim.industry_depth(node)`; each line goes when its last caller reads the view or sends the command itself."""
from sim.knowledge.api import NoteTechniquesChanged
from sim.markets.api import ResetMarketCaches
from sim.materials.api import ForgetReadings
from sim.projects.api import WatchActive
from sim.production.api import ForgetRevenueCaches, RefreshDoneCaches, RefreshOperatingCaches, constants

from sim.ventures.api import NoteOperatingChanged

from . import money_units, node_rederive, society_holdings


class ForwardProductionMixin:

	# the numbers other topics' code, the screens and the tests still read off the game (sim/production/constants.py declares them)
	vars().update({name: value for name, value in vars(constants).items() if name.isupper()})
	REVENUE_CEILING_PER_POP_SCALE = money_units.PricedInLabourHours("REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE")
	CAPABILITY_FACTOR_HALF_SATURATION_REV = money_units.PricedInLabourHours("CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS")
	INSTITUTION_PLACES_FALLBACK_UPKEEP_PER_HEAD = money_units.PricedInLabourHours(
		"INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD")

	# ---- what is running ----

	# ---- revenue and upkeep ----

	# ---- what a concern sells and takes ----

	# ---- industry experience ----

	# ---- the techniques in use ----

	# ---- the memos over what is done and operating ----
	# The production module keeps the memos; the hooks tell it, and the owners of the facts (knowledge, ventures, projects) count the change, the moment each one is stale.

	def _done_changed(self):
		"""Call after anything adds to or removes from the set of techniques done (or granted)."""
		self.send(RefreshDoneCaches())
		self.send(NoteTechniquesChanged())

	def _operating_changed(self):
		"""Call after anything adds to or removes from what is operating."""
		self.send(RefreshOperatingCaches())
		self.send(NoteOperatingChanged())

	def _reset_operating(self):
		"""Point the seat's business at the invalidation hook and invalidate once."""
		self.state.projects.business.watch = self._operating_changed
		self._operating_changed()

	def _reset_active(self):
		"""The acting seat's projects in hand report their changes from here on (a seat switch or a load needs it again)."""
		self.send(WatchActive(self.state.acting_seat))

	def _reset_economic_caches(self):
		"""Wipe all transient economic derived-state caches and re-wrap containers on save/load and on a seat switch."""
		self.send(ForgetRevenueCaches())
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
