"""The state seats owns, once per seat."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

HOUSEHOLD_SEAT = "household"
COUNTRY_SEAT = "country"   # a seat holding a country's government, with no household or founder of its own


@dataclass
class SeatsSeat:
    # the node the seat plays toward, the civilisation it plays for (None: the game's own), its kind, a country seat's
    # government actor id, and the standing policy switches the automatic mechanisms read (a flag, or a mode such as "replace")
    goal: Optional[str] = None
    country: Optional[str] = None
    kind: str = HOUSEHOLD_SEAT
    holder: Optional[str] = None
    policy: Dict[str, Any] = field(default_factory=dict)
    # whether the seat's founder lives, the years the founder has left, and why the seat's run ended (None while it plays)
    founder_alive: bool = True
    life_left: float = 40.0
    dead_reason: Optional[str] = None
    # the years in a row the seat's programme has had no director to carry it (the dissolution count)
    stalled: int = 0
    # the year the seat's formal goal was reached, and the year each goal id was reached as the formal goal
    goal_year: Optional[int] = None
    goal_years: Dict[str, int] = field(default_factory=dict)
    # rights and equity the seat holds as an actor: patents by node id, shares held by issuer id, and the part of the
    # seat's own equity issued to others
    patents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    shares_held: Dict[str, float] = field(default_factory=dict)
    shares_issued: float = 0.0
    # offers other actors have made the seat (plain dicts, as the exchange keeps them) and how many it has made
    offers: List[Dict[str, Any]] = field(default_factory=list)
    offer_serial: int = 0
