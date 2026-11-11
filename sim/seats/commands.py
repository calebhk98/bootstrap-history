"""The commands the seats module owns. The registry's own (`AddSeat`, `MoveSeat`) are the assembly's: it keeps each seat's record."""
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
class RememberGoalFloor(Command):
    """Keep `years`, the shortest road in years to the acting seat's goal, for every reader of it (applied by the seats module)."""
    years: float


@dataclass(frozen=True)
class RememberGoalClosure(Command):
    """Keep `nodes`, the set of nodes the acting seat's goal needs, for every reader of it (applied by the seats module)."""
    nodes: Any


@dataclass(frozen=True)
class ForgetGoalClosure(Command):
    """Drop what the acting seat's goal was found to need, and the road in years to it (applied by the seats module); the next ask works them out again."""


@dataclass(frozen=True)
class SetSeatHolder(Command):
    """The acting country seat holds the government whose actor id is `holder` (applied by the seats module)."""
    holder: str


@dataclass(frozen=True)
class EndRun(Command):
    """The acting seat's run ends for `reason` (None clears it). Announced in the seat's log unless `announce` is False."""
    reason: Optional[str]
    announce: bool = True


@dataclass(frozen=True)
class SetFounderLife(Command):
    """The acting seat's founder is alive with `years` left."""
    years: float


@dataclass(frozen=True)
class SetPolicy(Command):
    """The acting seat's standing policy switch `name` is now `value` (a flag, or a mode such as "replace")."""
    name: str
    value: Any


@dataclass(frozen=True)
class ReleasePatent(Command):
    """The seat `seat_id` gives up its right on `node_id` to `taker_id`, who is struck from its licensees. Answers the right."""
    seat_id: str
    node_id: str
    taker_id: str


@dataclass(frozen=True)
class ReceivePatent(Command):
    """The seat `seat_id` holds the right `entry` ({granted, expires, licensees}) on `node_id`."""
    seat_id: str
    node_id: str
    entry: Dict[str, Any]


@dataclass(frozen=True)
class AddLicensee(Command):
    """`licensee_id` may practise the invention the seat `seat_id` has patented on `node_id`."""
    seat_id: str
    node_id: str
    licensee_id: str


@dataclass(frozen=True)
class GiveShares(Command):
    """The seat `seat_id` gives `share` of `issuer_id`'s equity (`own_issue`: its own equity, issued to the taker)."""
    seat_id: str
    issuer_id: str
    share: float
    own_issue: bool


@dataclass(frozen=True)
class TakeShares(Command):
    """The seat `seat_id` takes `share` of `issuer_id`'s equity (`own_issue`: its own equity, bought back)."""
    seat_id: str
    issuer_id: str
    share: float
    own_issue: bool


@dataclass(frozen=True)
class KeepOffer(Command):
    """The seat `seat_id` has been made `offer` and keeps it until it answers or it lapses."""
    seat_id: str
    offer: Dict[str, Any]


@dataclass(frozen=True)
class DropOffer(Command):
    """The seat `seat_id` no longer holds the offer named `offer_id` (accepted or declined)."""
    seat_id: str
    offer_id: str


@dataclass(frozen=True)
class DropLapsedOffers(Command):
    """The seat `seat_id` drops the offers whose last year is before `year`. Answers their ids."""
    seat_id: str
    year: int


@dataclass(frozen=True)
class NextOfferSerial(Command):
    """The seat `seat_id` has made one more offer. Answers the count, which numbers the offer."""
    seat_id: str


@dataclass(frozen=True)
class PlaceSpies(Command):
    """The acting seat funds `count` spies against another seat (zero withdraws them). They cost a year's labour each, every year,
    and lapse when the purse cannot pay. Answers the count placed, or a Refusal that changed nothing."""
    target_id: str
    count: int
