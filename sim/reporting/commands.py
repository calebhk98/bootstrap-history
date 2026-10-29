"""Commands to reporting, the owner of the seat's log and the automation audit trail."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class RecordEvent(Command):
    """A line of a seat's log, stamped with the year, with the `kind` a reader tests and the `facts` the text states.
    `seat` names the seat whose log it is; None is the acting seat. `year` is the year the event belongs to; None is
    the current year."""
    kind: str
    text: str
    facts: Dict[str, Any] = field(default_factory=dict)
    seat: Optional[str] = None
    year: Optional[int] = None

    @classmethod
    def of(cls, kind: str, text: str, **facts: Any) -> "RecordEvent":
        return cls(kind, text, facts)

    @classmethod
    def in_year(cls, year: int, kind: str, text: str, **facts: Any) -> "RecordEvent":
        return cls(kind, text, facts, None, year)

    @classmethod
    def from_line(cls, line: Any, seat: Optional[str] = None, year: Optional[int] = None) -> "RecordEvent":
        """The event for a ready `LogLine` (sim/refusal.py): its kind, text and facts."""
        return cls(line.cause, str(line), dict(line.facts), seat, year)


@dataclass(frozen=True)
class DiscardEventsAfter(Command):
    """Drop the acting seat's log lines after the first `kept`: a trial that logged as it ran takes its lines back."""
    kept: int


@dataclass(frozen=True)
class RecordAutomation(Command):
    """A row of the automation audit trail for something automation did; the row's cost is how far the
    acting seat's capital has fallen since `capital_before`. Answers the row."""
    policy: str
    action: str
    what: str
    reason: str
    capital_before: float
    facts: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecordAutomationSkip(Command):
    """A row of the audit trail for something automation looked at and did not do. Answers the row."""
    policy: str
    what: str
    reason: str
    facts: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CloseRealOutput(Command):
    """Measure the year's real output per head once the market has closed, and note the price at which each good
    households newly want was first offered."""


@dataclass(frozen=True)
class ErodeMoney(Command):
    """The coin buys `share` less than it did (debasement): the purchasing-power indicator falls by that share."""
    share: float


@dataclass(frozen=True)
class NoteWageShock(Command):
    """The acting seat's cause book records that a shock named `cause` moved the wage index by `change`."""
    cause: str
    change: float


@dataclass(frozen=True)
class NoteConcernChange(Command):
    """The acting seat's cause book records that a concern opened or closed: `kind` is "opening" or "closure", `cause` the
    reason, and the row carries what the node earns (`revenue`) and costs (`upkeep`) a year."""
    kind: str
    node_id: str
    cause: str
    revenue: float
    upkeep: float


@dataclass(frozen=True)
class CloseCausePeriod(Command):
    """End the acting seat's open cause period: stamp its rows with the year and add what the year's change leaves unnamed."""
