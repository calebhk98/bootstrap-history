"""The state seats owns, once per seat."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SeatsSeat:
    # whether the seat's founder lives, the years the founder has left, and why the seat's run ended (None while it plays)
    founder_alive: bool = True
    life_left: float = 40.0
    dead_reason: Optional[str] = None
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
