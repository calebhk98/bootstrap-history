"""The projects module: the whole life of a project, from whether it may begin to what finishing or failing it does.

It owns the start (the legality test and its list of blockers, the commands, the year's automatic start), the progress
of a project in hand (founder hours, hired trades, bills, risk and calendar), its completion or failure, a node's
exclusions and rebuild, the gates a node puts on works that must be running, and the staffing rule of the works built
(closing what nobody can supervise, reopening it, warning first, auto-opening what pays, mothballing and restoring).

The projects in hand are its seat state, written only by its commands and watched so that any change of one moves the seat's
`active_projects_version`. What is built and running is the ventures module's: the module reads it through that module's views
and shuts, restores and reviews works by its commands."""
from sim.assembly.api import Module

from .allocation_notes import AllocationNotes
from .auto_open import AutoOpen
from .blocker_rules import START_CHECKS
from .blocker_views import BlockerViews
from .closures import Closures
from .completion import Completion
from .cost_tail import CostTail
from .costs import Costs
from .exclusions import Exclusions
from .hour_queue import HourQueue
from .mothball import Mothball
from .open_gate import OpenGate
from .project_order import ProjectOrder
from .precaution import Precaution
from .progress_hours import ProgressHours
from .progress_phase import ProgressPhase
from .rebuild import Rebuild
from .risk import Risk
from .running_gates import RunningGates
from .staffing import Staffing
from .staffing_report import StaffingReport
from .staffing_shortfall import StaffingShortfall
from .start_checks import StartChecks
from .start_phase import StartPhase
from .starting import Starting
from .trade_wait import TradeWait
from .applied import Applied


class Projects(Module):

	START_CHECKS = START_CHECKS   # the start test, in order; a mod's layer over the module replaces it

	PARTS = {
		"applied": Applied,
		"start_checks": StartChecks,
		"blocker_views": BlockerViews,
		"starting": Starting,
		"start_phase": StartPhase,
		"progress_phase": ProgressPhase,
		"progress_hours": ProgressHours,
		"risk": Risk,
		"precaution": Precaution,
		"completion": Completion,
		"rebuild": Rebuild,
		"running_gates": RunningGates,
		"closures": Closures,
		"exclusions": Exclusions,
		"open_gate": OpenGate,
		"hour_queue": HourQueue,
		"allocation_notes": AllocationNotes,
		"cost_tail": CostTail,
		"costs": Costs,
		"staffing": Staffing,
		"staffing_shortfall": StaffingShortfall,
		"staffing_report": StaffingReport,
		"auto_open": AutoOpen,
		"mothball": Mothball,
		"trade_wait": TradeWait,
		"project_order": ProjectOrder,
	}
