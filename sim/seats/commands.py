"""The commands the seats module owns. Seat registry commands (`RegisterSeat`, `MoveSeat`) are applied by the engine
bridge while the registry stays on `Sim`."""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class JoinSeat(Command):
    """Add a player from data (`template`: capital or kit, country, base_tile, starting_techs, scholars, artisans, goal,
    kind). Answers None, or a Refusal that changed nothing."""
    seat_id: str
    template: Dict[str, Any]


@dataclass(frozen=True)
class JoinCastSeats(Command):
    """Add the seats the civilisation's cast lists for the start of the game. Answers their ids."""


@dataclass(frozen=True)
class HandOverSeat(Command):
    """Pass `from_id`'s seat to `to_id`. Answers what moved, or a Refusal that changed nothing."""
    from_id: str
    to_id: str


@dataclass(frozen=True)
class SetGoal(Command):
    """Make a node the acting seat's formal goal; a goal reached before keeps the year it was reached in."""
    node_id: Optional[str]


@dataclass(frozen=True)
class RecordGoalReached(Command):
    """Note the year a node was reached; the acting seat's formal goal year follows when it is the goal."""
    node_id: str
    year: int


@dataclass(frozen=True)
class ApplyForPatent(Command):
    """The acting seat applies for the exclusive right to an invention it holds. Answers a reply dict."""
    node_id: Any


@dataclass(frozen=True)
class MakeOffer(Command):
    """The acting seat offers another actor or seat things for things. Answers a reply dict."""
    to: Any
    give: Any
    take: Any


@dataclass(frozen=True)
class AnswerOffer(Command):
    """The acting seat accepts or declines an offer made to it. Answers a reply dict."""
    offer_id: Any
    accept: bool


@dataclass(frozen=True)
class RegisterSeat(Command):
    """Put a new seat in the seat registry (applied by the engine, which keeps the registry): built from `template`
    with `capital` in the society's coin and `founder_years` of life."""
    seat_id: str
    template: Dict[str, Any]
    capital: float
    founder_years: float


@dataclass(frozen=True)
class MoveSeat(Command):
    """Move `from_id`'s seat to `to_id` in the registry and rename it in every store keyed by seat id (applied by the
    engine). The module's own stores are renamed by the module."""
    from_id: str
    to_id: str


@dataclass(frozen=True)
class ForgetGoalCaches(Command):
    """Drop everything the engine derived from the acting seat's goal (applied by the engine)."""


@dataclass(frozen=True)
class EndRun(Command):
    """The acting seat's run ends for `reason` (None clears it). Announced in the seat's log unless `announce` is False."""
    reason: Optional[str]
    announce: bool = True


@dataclass(frozen=True)
class SetFounderLife(Command):
    """The acting seat's founder is alive with `years` left."""
    years: float
