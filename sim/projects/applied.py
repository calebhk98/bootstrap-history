"""The projects module's change counters, command handlers and the views that are not a topic of their own."""
from sim.assembly.api import Part
from sim.invalidating import _InvalidatingDict

from .channels import ACTIVE, ACTIVE_CHANGES, START
from .halting import halt_active_projects
from .review import SeatReview


class Applied(Part):

	def __init__(self, module):
		super().__init__(module)
		self.spent_this_year = 0.0   # what the seat now stepping has paid on projects so far this year (not saved: a year's close empties it)

	def active_projects_version(self):
		"""The change counter of the acting seat's projects in hand, for memos over them: moves with every change of any project
		in hand (progress too), so a memo that depends on which projects are active should also key on those."""
		return self.seat_version(ACTIVE_CHANGES)

	def active_changed(self):
		"""A project in hand of the acting seat was added, removed or changed."""
		self.bump_seat(ACTIVE_CHANGES)

	def apply_watch_active(self, command):
		self._watch_active(command.seat_id)

	def _watch_active(self, seat_id):
		seat = self.seat_of(seat_id)
		watched = seat.active
		if not (isinstance(watched, _InvalidatingDict) and watched._on_change == self.active_changed):   # wrapped once per seat
			seat.active = _InvalidatingDict(watched, on_change=self.active_changed)
		self.bump_seat(ACTIVE_CHANGES, seat_id)

	def seat_bound(self):
		"""The acting seat's projects in hand report their changes from here on."""
		self._watch_active(self.clock.acting_seat)

	def apply_note_year_spend(self, command):
		self.spent_this_year += command.amount

	def apply_close_spend_year(self, command):
		self.seat.spend_last_year = self.spent_this_year
		self.spent_this_year = 0.0

	def apply_start_project(self, command):
		answer = self.parts.starting.start_project(command)
		self.bump_seat(ACTIVE)
		return answer

	def apply_stop_project(self, command):
		answer = self.parts.starting.stop_project(command)
		self.bump_seat(ACTIVE)
		return answer

	def apply_post_bounty(self, command):
		answer = self.parts.starting.post_bounty(command)
		self.bump_seat(ACTIVE)
		return answer

	def apply_bribe(self, command):
		return self.parts.starting.bribe(command)

	def apply_reset_project_progress(self, command):
		"""A sack burns the site: every project in hand goes back to the beginning, all its work left and none of its years done."""
		active = self.seat.active
		nodes = self.needs.tree_nodes()
		for node_id in sorted(active):
			active[node_id]["ph_left"] = nodes[node_id]["ph"]
			active[node_id]["yrs"] = 0.0
		self.bump_seat(ACTIVE)

	def apply_complete_project(self, command):
		self.parts.completion.complete(command.node_id)
		self.bump_seat(ACTIVE)

	def apply_close_work(self, command):
		self.parts.closures.close_work(command.node_id, command.reason, command.year, command.cascade)

	def apply_close_lapsed_dependents(self, command):
		return self.parts.running_gates.close_lapsed_dependents(command.year)

	def apply_close_unstaffed_ventures(self, command):
		return self.parts.staffing.close_unstaffed_ventures(command.year)

	def apply_reopen_restaffed_ventures(self, command):
		return self.parts.staffing.reopen_restaffed_ventures(command.year)

	def apply_auto_open_ventures(self, command):
		return self.parts.auto_open.auto_open_ventures()

	def apply_note_venture_year(self, command):
		self.parts.staffing.note_venture_year()

	def apply_review_ventures(self, command):
		return self.parts.staffing.review_ventures(command.rules, command.year)

	def apply_halt_active_projects(self, command):
		if not self.seat.active:
			return [], 0.0
		halted = halt_active_projects(self.seat.active, self.seat.paid_towards, self.seat.bountied)
		self.bump_seat(ACTIVE)
		return halted

	def apply_mothball_work(self, command):
		return self.parts.mothball.mothball_work(command.node_id)

	def apply_restore_work(self, command):
		return self.parts.mothball.restore_work(command.node_id)

	def start_projects_hook(self, seat_id):
		self.parts.start_phase.start_projects_phase(seat_id)
		self.bump_seat(START)

	def last_start(self):
		return self.parts.starting.last_materials_paid

	def active_projects(self):
		"""{node id: the project's record} of the acting seat's projects in hand (the object itself)."""
		return self.seat.active

	def active_project_ids(self):
		"""The ids of the acting seat's projects in hand, in id order (not the order they were started)."""
		return sorted(self.seat.active)

	def bountied_nodes(self):
		"""The nodes the acting seat has posted a bounty on (the live set)."""
		return self.seat.bountied

	def failed_attempt_counts(self):
		"""{node id: how many times the acting seat's attempt at it has failed} (the live record)."""
		return self.seat.failed_attempts

	def paid_towards_projects(self):
		"""{node id: the money already paid into the project in hand} for the acting seat (the live record)."""
		return self.seat.paid_towards

	def bounties_paid_total(self):
		"""How many bounties the acting seat's household has paid out."""
		return self.seat.bounties_paid

	def shut_for_staff(self):
		"""{work id: the year it was shut} of the acting seat's works closed for want of staff."""
		return {node_id: record["year"] for node_id, record in self.needs.closure_records().items() if record["reason"] == "staff"}

	def spend_last_year(self):
		"""What the acting seat spent on projects in the year just closed, or None before the first year ends."""
		return self.seat.spend_last_year

	def committed_cost(self):
		"""What is still owed, in total, across every project in hand: they all draw on the same purse and the same credit
		line."""
		return sum(self.seat.active[node_id].get("cost_left") or 0.0 for node_id in sorted(self.seat.active))

	def reputation_gain_of_node(self, node_id):
		"""The standing finishing `node_id` adds."""
		return self.parts.completion.reputation_gain_of(self.needs.tree_nodes()[node_id])

	def seat_review(self, world, year):
		"""The founder's seat's answers to a business review."""
		return SeatReview(self.module, world, year)
