"""Reporting's module spec (sim/assembly)."""
from sim.assembly.api import QUOTE, TABLE, ModuleSpec, PhaseHook, ViewSpec

from .commands import DiscardEventsAfter, RecordAutomation, RecordAutomationSkip, RecordEvent
from .log import AUDIT, LOG
from .module import Reporting
from .state import ReportingSeat

MODULE_SPECS = (ModuleSpec(
    "reporting", Reporting, channels=(LOG, AUDIT), seat_state=ReportingSeat,
    publishes=(
        # cached: every write to the log is a command of this module
        ViewSpec("event_log", "event_log", kind=TABLE, channels=(LOG,), seat_scoped=True),
        ViewSpec("automation_rows", "automation_rows", kind=QUOTE, seat_scoped=True),
    ),
    applies=((RecordEvent, "record_event"), (DiscardEventsAfter, "discard_events_after"),
             (RecordAutomation, "record_automation"), (RecordAutomationSkip, "record_automation_skip")),
    reads=("year", "acting_balance"),
    phases=(PhaseHook("trim_audit", "trim_audit"),),
),)
