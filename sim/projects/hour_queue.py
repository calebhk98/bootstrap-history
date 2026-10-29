"""Who gets the founder's hours first: the one queue the allocator and every screen read, so a displayed rank is the rank
the next step applies."""
from .hour_offer import priority_queue


class HourQueue:
	def hour_priority_queue(self):
		"""Active projects in the order they draw on the hour pool: projects with a standing `allocate` first, then the
		rest by tree priority."""
		return priority_queue(self.seat.active, self.needs.project_order(),
		                      self.needs.hour_commitments()["allocations"])

	def hour_pool_now(self):
		"""Founder and deputy hours this year not already committed."""
		hours = self.needs.hours_available
		return max(0.0, hours["director_pool"] - hours["director_committed"])

	def hour_standing(self, node_id):
		"""(rank, active count, pool) for a project in hand, from today's active list; None when it is not in hand."""
		queue = self.hour_priority_queue()
		if node_id not in queue:
			return None
		return queue.index(node_id) + 1, len(queue), self.hour_pool_now()
