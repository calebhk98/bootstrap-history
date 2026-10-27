"""The ventures module: what a seat's concerns tie up and cost, opening one by hand, the founder's sales and the roll-out of
public works.

It owns no saved state yet: the businesses and their plants stay in the projects record (`legacy_projects`), which production,
finance, hazards and the household facade still write, so every view it publishes is uncached."""
from sim.assembly.api import Module

from .coverage import Coverage
from .crew import Crew
from .opening import Opening
from .quotes import Quotes
from .sales import Sales


class Ventures(Crew, Quotes, Opening, Sales, Coverage, Module):

	# ---- views under the names other modules read them by ----

	def closures(self):
		"""The works the seat has shut and may reopen (the live set)."""
		return self.needs.legacy_projects().mothballed

	def concern_staff(self, node_id):
		return self.concern_staff_by_trade(node_id)

	def venture_opened_year(self, node_id, default):
		"""The year the plant first opened, or `default` where nothing records it."""
		return self.needs.legacy_projects().business.opened_year_of(node_id, default)

	# ---- the commands ----

	def apply_open_venture(self, command):
		return self.open_venture(command.node_id, units=command.units)

	def apply_clear_mothball(self, command):
		self.needs.legacy_projects().mothballed.discard(command.node_id)

	def apply_sell_concern(self, command):
		return self.sell_concern(command.node_id)

	def apply_roll_out(self, command):
		return self.roll_out(command.node_id, command.share)
