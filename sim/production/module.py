"""The production module: what runs, what it earns and costs, and how established each industry is.

It answers which of the acting seat's techniques and capabilities are running, what its concerns take in and cost to keep this year,
what a concern makes from the techniques its society runs, how deep an industry's experience is, and which techniques some producer
uses. It owns each seat's stock of industry experience (`ProductionSeat`) and the memos over what is done and operating (`caches`).
The record of what is done, operating and granted, the tree and the economy's objects have not moved yet, so the module reads them
through the views of their owners and every view it publishes is uncached: legacy code writes that state directly. The engine's
household hooks drop the memos by sending the commands here."""
from sim.assembly.api import Module

from . import caches
from .book_sales import BookSales
from .capability import Capability
from .concern_market import ConcernMarket
from .constants import INSTITUTION_EXPANSION_CONVEXITY, RAMP_SHARE_AT_FULL_DEPTH
from .depth import Depth
from .learning import Learning
from .revenue import Revenue
from .techniques import Techniques
from .upkeep import Upkeep
from .volume import Volume


class Production(Revenue, Upkeep, ConcernMarket, BookSales, Volume, Learning, Depth, Techniques, Capability, Module):

	def setup(self):
		self._memos = {}   # acting seat -> its SeatMemos; never saved

	def memos(self):
		"""The acting seat's remembered figures."""
		seat_id = self.clock.acting_seat
		memos = self._memos.get(seat_id)
		if memos is None:
			memos = self._memos[seat_id] = caches.SeatMemos()
		return memos

	# ---- what the engine's other objects still hold, as views ----

	def done_in_order(self):
		"""Everything the acting seat has finished, in the tree's own order (the memo lives here)."""
		return self.memos().done_in_order(self.needs.tree_nodes(), self.needs.techniques_held())

	def running_stamp(self):
		"""(the done set, the counts and versions of what is built, granted and operating, the tree): a table derived from what is
		running stays good while this is unchanged."""
		done = self.needs.techniques_held()
		return (done, (self.needs.techniques_version(), self.needs.operating_version(), len(done), len(self.needs.techniques_granted()),
		               len(self.needs.operating())), self.needs.tree_nodes())

	def practice_set(self):
		return self._practice_set()

	def practisable(self, node_id):
		return self._practisable(node_id)

	def institution_expansion_convexity(self):
		return INSTITUTION_EXPANSION_CONVEXITY

	def ramp_share_at_full_depth(self):
		return RAMP_SHARE_AT_FULL_DEPTH

	def failed_attempts_trial(self, node_id, count):
		"""The industry's stock as it would stand after `count` more diagnosed failures, as a scope to read the odds inside."""
		return self.after_failed_attempts(node_id, count)

	# ---- the commands ----

	def apply_refresh_done_caches(self, command):
		self.memos().forget_done()

	def apply_refresh_operating_caches(self, command):
		self.memos().forget_operating()

	def seat_bound(self):
		"""Every seat's memos over what is done and operating are dropped, to be rebuilt."""
		self._memos.clear()

	def apply_accrue_experience(self, command):
		self.accrue_industry_experience()

	def apply_learn_from_failure(self, command):
		self.learn_from_failed_attempt(command.node_id)
