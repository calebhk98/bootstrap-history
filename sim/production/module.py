"""The production module: what runs, what it earns and costs, and how established each industry is.

It answers which of the acting seat's techniques and capabilities are running, what its concerns take in and cost to keep this year,
what a concern makes from the techniques its society runs, how deep an industry's experience is, and which techniques some producer
uses. It owns each seat's stock of industry experience (`ProductionSeat`). The record of what is done, operating and granted, the
household, the tree and the economy's objects have not moved yet, so the module reaches them through `legacy_game` and every view it
publishes is uncached: legacy code writes that state directly. The revenue and candidate caches live on the household object because
the engine drops them through `caches` (its household hooks call the same functions the commands here do)."""
from sim.assembly.api import Module

from . import caches
from .book_sales import BookSales
from .capability import Capability
from .concern_market import ConcernMarket
from .constants import RAMP_SHARE_AT_FULL_DEPTH
from .depth import Depth
from .learning import Learning
from .revenue import Revenue
from .techniques import Techniques
from .upkeep import Upkeep
from .volume import Volume


class Production(Revenue, Upkeep, ConcernMarket, BookSales, Volume, Learning, Depth, Techniques, Capability, Module):

	def _game(self):
		game = self.__dict__.get("_sim")
		if game is None:
			game = self._sim = self.needs.legacy_game()
		return game

	# ---- what the engine's other objects still hold, as views ----

	def operating(self):
		"""The acting seat's concerns and capabilities that are open (the live set: the engine adds and discards in place)."""
		return self._game().state.projects.operating

	def done_in_order(self):
		"""Everything the acting seat has finished, in the tree's own order (the memo lives on the household)."""
		game = self._game()
		return caches.done_in_order(game.household, game.nodes, game.state.projects.done)

	def running_stamp(self):
		"""(the projects record, the counts and versions of what is built, granted and operating, the tree): a table derived
		from what is running stays good while this is unchanged."""
		game = self._game()
		projects = game.state.projects
		return (projects, (game.household.done_version, game.household.operating_version,
		                   len(projects.done), len(projects.granted), len(projects.operating)), game.nodes)

	def practice_set(self):
		return self._practice_set()

	def practisable(self, node_id):
		return self._practisable(node_id)

	def ramp_share_at_full_depth(self):
		return RAMP_SHARE_AT_FULL_DEPTH

	def failed_attempts_trial(self, node_id, count):
		"""The industry's stock as it would stand after `count` more diagnosed failures, as a scope to read the odds inside."""
		return self.after_failed_attempts(node_id, count)

	# ---- the commands ----

	def apply_refresh_done_caches(self, command):
		caches.forget_done(self._game().household)

	def apply_accrue_experience(self, command):
		self.accrue_industry_experience()

	def apply_learn_from_failure(self, command):
		self.learn_from_failed_attempt(command.node_id)
