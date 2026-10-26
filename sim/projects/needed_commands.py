"""Commands the projects module sends to owners that have not moved into modules yet.

Each is applied by the engine bridge (sim/engine/bridge_projects.py) exactly as the old code did. When the owner moves
it takes the class into its own package and applies it; this file loses the entry and the importers follow."""
from dataclasses import dataclass, field
from typing import Any, Dict

from sim.assembly.api import Command


@dataclass(frozen=True)
class RecordEvent(Command):
    """Reporting: a line of the acting seat's log, stamped with the year, with the `kind` a reader tests."""
    kind: str
    text: str


@dataclass(frozen=True)
class RecordAutomation(Command):
    """Reporting: a row of the automation audit trail for something automation did; the row's cost is how far the
    acting seat's capital has fallen since `capital_before`."""
    policy: str
    action: str
    what: str
    reason: str
    capital_before: float
    facts: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecordAutomationSkip(Command):
    """Reporting: a row of the audit trail for something automation looked at and did not do."""
    policy: str
    what: str
    reason: str
    facts: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SettleProjectMaterials(Command):
    """Materials: buy the materials the market can deliver now for the project (when the money can be raised) and
    bank them. Answers (what is left to pay in instalments, the materials money paid now)."""
    node_id: str


@dataclass(frozen=True)
class ClearMothball(Command):
    """Ventures: forget a stale mothball entry for a work that is being built again."""
    node_id: str


@dataclass(frozen=True)
class CompleteProject(Command):
    """Projects' own completion (not moved yet): finish the project at once, as an instantaneous capability does."""
    node_id: str
