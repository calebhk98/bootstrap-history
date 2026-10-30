"""The materials module's commands: what any actor sends to take the year's material reading or to buy a project's materials.
Each acts on the acting seat."""
from dataclasses import dataclass
from typing import Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class ApplyThrottle(Command):
    """Read the year's material pace now and bank what it leaves: the unused part of the seat's own output and stock goes
    back into the tonnes ledger, the market's draw is noted, a pool that binds is counted as a shortage. A repeat with
    nothing changed since replays the last reading. Answers the pace (the share of planned work the materials and
    electricity support), or with `node_id` that project's pace: full unless it draws on the pool that binds."""
    node_id: Optional[str] = None


@dataclass(frozen=True)
class SettleProjectMaterials(Command):
    """Buy the materials the market can deliver now for a project (when the money can be raised) and bank them. Answers
    (what is left to pay in instalments, the materials money paid now)."""
    node_id: str


@dataclass(frozen=True)
class RestoreReadings(Command):
    """The demand the last throttle saw, as the save kept it, becomes the acting seat's remembered demand (after a load)."""


@dataclass(frozen=True)
class CaptureReadings(Command):
    """The acting seat's remembered demand is written into its saved state (before a save)."""
