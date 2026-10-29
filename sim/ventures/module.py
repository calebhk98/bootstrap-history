"""The ventures module: the seat's businesses and the plants they run, what a seat's concerns tie up and cost, opening one by
hand, the founder's sales and the roll-out of public works.

The businesses are its seat state, written only by its commands (a deal's plants pass by `ReleasePlant` and `AdoptPlant`). The views
over what is operating and shut hand out the record's own sets, read only, and are uncached."""
from sim.agents.api import FounderReview
from sim.assembly.api import Module
from sim.production.api import RefreshOperatingCaches

from .channels import INSTITUTION_UNITS_CHANGES, OPERATING_CHANGES
from .coverage import Coverage
from .crew import Crew
from .opening import Opening
from .quotes import Quotes
from .sales import Sales


class Ventures(Crew, Quotes, Opening, Sales, Coverage, Module):

	# ---- views under the names other modules read them by ----

	def mothballed(self):
		"""The works the acting seat has shut and may reopen (the live set)."""
		return self.seat.business.mothballed()

	def closure_records(self):
		"""{work id: {"reason", "year"}} of the shut works that record why (a live mapping, read only)."""
		return self.seat.business.closures()

	def operating(self):
		"""The acting seat's concerns and capabilities that are open (the live set: the plants opened and closed change it in place)."""
		return self.seat.business.operating()

	def operating_by_seat(self):
		"""What every seat has open, by seat id in joining order (the live sets)."""
		return {seat_id: self.seat_of(seat_id).business.operating() for seat_id in self.needs.seat_list()["joined"]}

	def operating_version(self):
		"""The change counter of what the acting seat has open, for memos over it: moves with every plant opened or closed."""
		return self.seat_version(OPERATING_CHANGES)

	def institution_units_version(self):
		"""The change counter of the sizes of the acting seat's scalable institutions, for memos over them."""
		return self.seat_version(INSTITUTION_UNITS_CHANGES)

	def concern_staff(self, node_id):
		return self.concern_staff_by_trade(node_id)

	def venture_opened_year(self, node_id, default):
		"""The year the plant first opened, or `default` where nothing records it."""
		return self.seat.business.opened_year_of(node_id, default)

	def venture_size(self, node_id):
		"""How many founding sizes the seat's plant of this concern is (one where it records none)."""
		return self.seat.business.size_of(node_id)

	# ---- the commands ----

	def operating_changed(self):
		"""A plant of a seat's business opened, shut or closed."""
		self.needs.send(RefreshOperatingCaches())
		self.bump_seat(OPERATING_CHANGES)

	def seat_bound(self):
		"""The acting seat's business reports its plants' opening and closing from here on; what is operating is told to have changed."""
		self.seat.business.watch = self.operating_changed
		self.operating_changed()

	def apply_watch_business(self, command):
		self.seat_of(command.seat_id).business.watch = self.operating_changed

	def apply_release_plant(self, command):
		plant = self.seat_of(command.seat_id).business.close_plant(command.node_id)
		if plant is not None and plant.opened_year is None:
			plant.opened_year = command.year
		return plant

	def apply_adopt_plant(self, command):
		self.seat_of(command.seat_id).business.adopt(command.plant)

	def apply_note_operating_changed(self, command):
		self.bump_seat(OPERATING_CHANGES)

	def apply_open_venture(self, command):
		return self.open_venture(command.node_id, units=command.units)

	def apply_clear_mothball(self, command):
		self.seat.business.mothballed().discard(command.node_id)

	def apply_shut_forgotten(self, command):
		for node_id in command.node_ids:
			self.seat.business.operating().discard(node_id)
			self.seat.business.mothballed().discard(node_id)

	def apply_stop_operating(self, command):
		for node_id in command.node_ids:
			self.seat.business.operating().discard(node_id)

	def apply_mothball_concern(self, command):
		self.seat.business.mothball(command.node_id, command.year, command.reason)

	def apply_restore_concern(self, command):
		self.seat.business.restore(command.node_id)

	def apply_close_concern(self, command):
		self.seat.business.close_plant(command.node_id)

	def apply_forget_closure_reason(self, command):
		return self.seat.business.forget_reason(command.node_id, command.reason)

	def apply_review_concerns(self, command):
		return self.seat.business.review(FounderReview(), self.needs.actor_world(), command.rules)

	def apply_review_reopening(self, command):
		return self.seat.business.review_reopening(FounderReview(), self.needs.actor_world())

	def apply_note_concern_year(self, command):
		self.seat.business.note_year(command.node_id, command.margin)

	def apply_sell_concern(self, command):
		return self.sell_concern(command.node_id)

	def apply_roll_out(self, command):
		return self.roll_out(command.node_id, command.share)
