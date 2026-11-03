"""The production module's views of what the acting seat has done and runs, its memos and its command handlers."""
from sim.assembly.api import Part

from . import caches
from .constants import INSTITUTION_EXPANSION_CONVEXITY, RAMP_SHARE_AT_FULL_DEPTH


class Views(Part):

	def __init__(self, module):
		super().__init__(module)
		self._memos = {}   # acting seat -> its SeatMemos; never saved

	def memos(self):
		"""The acting seat's remembered figures."""
		seat_id = self.clock.acting_seat
		memos = self._memos.get(seat_id)
		if memos is None:
			memos = self._memos[seat_id] = caches.SeatMemos()
		return memos

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
		return self.parts.revenue._practice_set()

	def practisable(self, node_id):
		return self.parts.revenue._practisable(node_id)

	def institution_expansion_convexity(self):
		return INSTITUTION_EXPANSION_CONVEXITY

	def ramp_share_at_full_depth(self):
		return RAMP_SHARE_AT_FULL_DEPTH

	def failed_attempts_trial(self, node_id, count):
		"""The industry's stock as it would stand after `count` more diagnosed failures, as a scope to read the odds inside."""
		return self.parts.depth.after_failed_attempts(node_id, count)

	def apply_refresh_done_caches(self, command):
		self.memos().forget_done()

	def apply_refresh_operating_caches(self, command):
		self.memos().forget_operating()

	def seat_bound(self):
		"""Every seat's memos over what is done and operating are dropped, to be rebuilt."""
		self._memos.clear()

	def apply_accrue_experience(self, command):
		self.parts.depth.accrue_industry_experience()

	def apply_learn_from_failure(self, command):
		self.parts.depth.learn_from_failed_attempt(command.node_id)
