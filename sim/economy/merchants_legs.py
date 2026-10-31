"""The destinations a merchant serves from one source: a route is a tuple of legs (destination tile, destination area, weight).

What the merchant holds on the source tile is carried along every leg in proportion to the legs' weights
(the units bought for each leg, or the room each destination has when nothing was bought).
"""
import math
from typing import Dict, Iterable, List, Mapping, Tuple

Leg = Tuple[str, str, float]


def split(legs: Iterable[Leg], quantity: float) -> List[Tuple[str, str, float]]:
    """(destination tile, area, units) for each leg, `quantity` shared by weight; equal shares when no leg has weight."""
    legs = list(legs)
    total = math.fsum(max(0.0, weight) for _tile, _area, weight in legs)
    if len(legs) == 1:
        return [(legs[0][0], legs[0][1], quantity)]
    if total <= 0.0:
        return [(tile, area, quantity / len(legs)) for tile, area, _weight in legs]
    return [(tile, area, quantity * (max(0.0, weight) / total)) for tile, area, weight in legs]


def from_weights(weights: Mapping[Tuple[str, str], float]) -> Tuple[Leg, ...]:
    """Legs, sorted by destination tile, from {(destination tile, area): weight}."""
    return tuple((tile, area, weight) for (tile, area), weight in sorted(weights.items()))


def held_weights(rooms: Dict[Tuple[str, str], float]) -> Dict[Tuple[str, str], float]:
    """Weights for stock already held: each destination's room, where it is finite; a destination with no limit
    (inf) weighs as much as the largest finite room, or one when none is finite. A destination with no room
    gets none."""
    finite = [room for room in rooms.values() if room != math.inf]
    unlimited = max(finite, default=1.0) or 1.0
    return {key: (unlimited if room == math.inf else room) for key, room in rooms.items() if room > 0.0}
