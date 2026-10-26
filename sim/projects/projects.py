"""The projects module: whether a project may begin and the commands that begin, stop and buy one.

What it owns of the project lifecycle is the start: the legality test and its list of blockers (start_checks.py,
blocker_views.py), the commands (starting.py) and the year's automatic start (start_phase.py). A project in hand
(`state.projects`) is still written by progress and completion, which have not moved, so the module reaches that state
through the engine bridge's `legacy_*` views; docs/architecture/MODULE_MIGRATION_TASKS.md lists them as debts."""
from sim.assembly.api import Module

from .blocker_views import BlockerViews
from .start_checks import StartChecks
from .start_phase import StartPhase
from .starting import Starting

ACTIVE = "active"        # the seat's projects in hand changed
START = "start"          # the seat's start phase measured the year's hours


class Projects(StartChecks, BlockerViews, Starting, StartPhase, Module):
	def setup(self) -> None:
		self._setup_start_checks()
		self._setup_starting()
		self._setup_start_phase()

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

	def start_projects_hook(self, seat_id):
		self.start_projects_phase(seat_id)
		self.bump_seat(START)

	def last_start(self):
		return self.last_materials_paid
