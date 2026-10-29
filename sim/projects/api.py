"""The projects package's only door."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine bridge hands it the legacy state it still needs

from sim.polity.api import RecordBribe
from .commands import (AdvanceProjects, AutoOpenVentures, Bribe, CloseLapsedDependents, CloseUnstaffedVentures, CloseWork,
                       CompleteProject, Exclude, Include, KeepStaffed, MothballWork, NoteVentureYear, PostBounty, PutProjectFirst, ReopenRestaffedVentures, ReorderProjects, ResetProjectProgress,
                       RestoreProjectOrder, RestoreWork, ReviewVentures, ShutForgotten, StartProject, StopProject)
from sim.materials.api import SettleProjectMaterials
from .needed_commands import NoteConcernChange, NoteYearSpend
from sim.reporting.api import RecordAutomation, RecordAutomationSkip, RecordEvent
from .blocker_rules import BLOCKER_KINDS, BLOCKER_MEANING, RUNNING_CONSTRAINT_KIND, START_CHECKS
from .state import ProjectsSeat
from .failure_text import FAILED_PREFIX, MINOR_MARK
from .goal_rules import goal_movement
from .permanent_benefit import permanent_parts
from .trade_demand import oversubscription_notes, trade_demand_table
from .training_words import training_advice_text
from . import (arrears_hours_line, auto_start, blocker_rules, bribe_rules, closure_grace, closure_reasons, completion_rules, completion_schedule,
               constants, exclusion_rules, failure_cause, failure_diagnosis, failure_text, funding, goal_rules, hour_offer,
               instantaneous, phase_rules, precaution_rules, progress_rules, rebuild_rules, record_rules, retry_calendar,
               risk_rules, running_gate_rules, staff_gate, staffing_choice, staffing_events, staffing_warning_rows, start_money,
               start_rules)
