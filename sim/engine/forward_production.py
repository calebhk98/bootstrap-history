"""One-line forwarders from the old `Sim` names of production to the production module, for callers not yet in a module.

The screens, the project phases, the agent economy's port, the labour core and the tests still say `sim.running(node)`, `sim.revenue()` or
`sim.industry_depth(node)`; each line goes when its last caller reads the view or sends the command itself."""
from sim.knowledge.api import NoteTechniquesChanged
from sim.production.api import RefreshDoneCaches, RefreshOperatingCaches, constants

from sim.ventures.api import NoteOperatingChanged

from . import money_units, node_rederive


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

	# ---- the tree's derived figures (composition: node_rederive.py) ----

	def refresh_derived_nodes(self):
		node_rederive.refresh_derived_nodes(self)

	def _remember_derived_gates(self, held_techs):
		node_rederive.remember_derived_gates(self, held_techs)

