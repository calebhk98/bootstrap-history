"""Commands to reporting, the owner of the log and the automation audit trail (applied by the engine bridge until
reporting moves into a module)."""
from dataclasses import dataclass, field
from typing import Any, Dict

from sim.assembly.api import Command


@dataclass(frozen=True)
class RecordEvent(Command):
    """A line of the acting seat's log, stamped with the year, with the `kind` a reader tests."""
    kind: str
    text: str


@dataclass(frozen=True)
class RecordAutomation(Command):
    """A row of the automation audit trail for something automation did; the row's cost is how far the
    acting seat's capital has fallen since `capital_before`."""
    policy: str
    action: str
    what: str
    reason: str
    capital_before: float
    facts: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecordAutomationSkip(Command):
    """A row of the audit trail for something automation looked at and did not do."""
    policy: str
    what: str
    reason: str
    facts: Dict[str, Any] = field(default_factory=dict)
