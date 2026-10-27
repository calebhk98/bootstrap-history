"""The projects module: the whole life of a project, from whether it may begin to what finishing or failing it does.

It owns the start (the legality test and its list of blockers, the commands, the year's automatic start), the progress
of a project in hand (founder hours, hired trades, bills, risk and calendar), its completion or failure, a node's
exclusions and rebuild, the gates a node puts on works that must be running, and the staffing rule of the works built
(closing what nobody can supervise, reopening it, warning first, auto-opening what pays, mothballing and restoring).

A project in hand (`state.projects`) and the record of what is built and running are still written by the engine's
unmoved parts (the screens, hazards, the credit freeze, ventures), so the module reaches that state through the engine
bridge's `legacy_*` views; docs/architecture/MODULE_MIGRATION_TASKS.md lists them as debts."""
from sim.assembly.api import Module

from .allocation_notes import AllocationNotes
from .auto_open import AutoOpen
from .blocker_views import BlockerViews
from .closures import Closures
from .completion import Completion
from .cost_tail import CostTail
from .costs import Costs
from .exclusions import Exclusions
from .hour_queue import HourQueue
from .mothball import Mothball
from .open_gate import OpenGate
from .precaution import Precaution
from .progress_hours import ProgressHours
from .progress_phase import ProgressPhase
from .rebuild import Rebuild
from .review import SeatReview
from .risk import Risk
from .running_gates import RunningGates
from .staffing import Staffing
from .staffing_report import StaffingReport
from .staffing_shortfall import StaffingShortfall
from .start_checks import StartChecks
from .start_phase import StartPhase
from .starting import Starting
from .trade_wait import TradeWait

ACTIVE = "active"        # the seat's projects in hand changed
START = "start"          # the seat's start phase measured the year's hours


class Projects(StartChecks, BlockerViews, Starting, StartPhase, ProgressPhase, ProgressHours, Risk, Precaution, Completion,
               Rebuild, RunningGates, Closures, Exclusions, OpenGate, HourQueue, AllocationNotes, CostTail, Costs, Staffing,
               StaffingShortfall, StaffingReport, AutoOpen, Mothball, TradeWait, Module):
	def setup(self) -> None:
		self._setup_start_checks()
		self._setup_starting()
		self._setup_start_phase()
		self._setup_rebuild()
		self._setup_running_gates()
		self._setup_completion()

	# ---- the commands ----

	def apply_start_project(self, command):
		answer = self.start_project(command)
		self.bump_seat(ACTIVE)
		return answer

	def apply_stop_project(self, command):
		answer = self.stop_project(command)
		self.bump_seat(ACTIVE)
		return answer

	def apply_post_bounty(self, command):
		answer = self.post_bounty(command)
		self.bump_seat(ACTIVE)
		return answer

	def apply_bribe(self, command):
		return self.bribe(command)

	def apply_reset_project_progress(self, command):
		"""A sack burns the site: every project in hand goes back to the beginning, all its work left and none of its years done."""
		active = self.needs.legacy_projects().active
		nodes = self.needs.tree_nodes()
		for node_id in sorted(active):
			active[node_id]["ph_left"] = nodes[node_id]["ph"]
			active[node_id]["yrs"] = 0.0
		self.bump_seat(ACTIVE)

	def apply_complete_project(self, command):
		self._complete(command.node_id)
		self.bump_seat(ACTIVE)

	def apply_close_work(self, command):
		self.close_work(command.node_id, command.reason, command.year, command.cascade)

	def apply_close_lapsed_dependents(self, command):
		return self.close_lapsed_dependents(command.year)

	def apply_close_unstaffed_ventures(self, command):
		return self.close_unstaffed_ventures(command.year)

	def apply_reopen_restaffed_ventures(self, command):
		return self.reopen_restaffed_ventures(command.year)

	def apply_auto_open_ventures(self, command):
		return self.auto_open_ventures()

	def apply_note_venture_year(self, command):
		self.note_venture_year()

	def apply_review_ventures(self, command):
		return self.review_ventures(command.rules, command.year)

	def apply_mothball_work(self, command):
		return self.mothball_work(command.node_id)

	def apply_restore_work(self, command):
		return self.restore_work(command.node_id)

	def start_projects_hook(self, seat_id):
		self.start_projects_phase(seat_id)
		self.bump_seat(START)

	# ---- views that are not a method of a topic ----

	def last_start(self):
		return self.last_materials_paid

	def active_projects(self):
		"""{node id: the project's record} of the acting seat's projects in hand (the object itself)."""
		return self.needs.legacy_projects().active

	def mothballed_works(self):
		"""The works the acting seat has mothballed (the live set)."""
		return self.needs.legacy_projects().mothballed

	def bountied_nodes(self):
		"""The nodes the acting seat has posted a bounty on (the live set)."""
		return self.needs.legacy_projects().bountied

	def failed_attempt_counts(self):
		"""{node id: how many times the acting seat's attempt at it has failed} (the live record)."""
		return self.needs.legacy_projects().failed_attempts

	def paid_towards_projects(self):
		"""{node id: the money already paid into the project in hand} for the acting seat (the live record)."""
		return self.needs.legacy_projects().paid_towards

	def bounties_paid_total(self):
		"""How many bounties the acting seat's household has paid out."""
		return self.needs.legacy_acting_household().bounties_paid

	def shut_for_staff(self):
		"""{work id: the year it was shut} of the acting seat's works closed for want of staff."""
		closures = self.needs.legacy_projects().closures
		return {node_id: record["year"] for node_id, record in closures.items() if record["reason"] == "staff"}

	def spend_last_year(self):
		"""What the acting seat's household spent on projects in the year just closed, or None before the first year ends."""
		return self.needs.legacy_acting_household().spend_last_year

	def committed_cost(self):
		"""What is still owed, in total, across every project in hand: they all draw on the same purse and the same credit
		line."""
		projects = self.needs.legacy_projects()
		return sum(projects.active[node_id].get("cost_left") or 0.0 for node_id in projects.active_keys_sorted())

	def reputation_gain_of_node(self, node_id):
		"""The standing finishing `node_id` adds."""
		return self.reputation_gain_of(self.needs.tree_nodes()[node_id])

	def seat_review(self, world, year):
		"""The founder's seat's answers to a business review."""
		return SeatReview(self, world, year)
