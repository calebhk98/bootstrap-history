"""The trade schools an actor owns, as the records the labour core trains through."""
from typing import Mapping, Tuple

from .market.records import School


def schools_of_actor(owner: str, area: str, seats_by_trade: Mapping[str, float]) -> Tuple[School, ...]:
    """One `School` per trade the actor holds seats in, in the area its seats are in (trades in id order); no seats, no school."""
    return tuple(School(owner=owner, trade=trade, area=area, seats=float(seats))
                 for trade, seats in sorted(seats_by_trade.items()) if seats > 0.0)
