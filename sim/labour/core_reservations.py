"""Reservations against the labour core's people, by tile and trade: a hire is taken out of the people the core
holds where the hire works, so nobody counts as free to one employer and hired by another. Complaint 556."""
from typing import Dict, List, Mapping, Tuple

PeopleByTileAndTrade = Mapping[str, Mapping[str, float]]


def free_people(core: PeopleByTileAndTrade, hires: PeopleByTileAndTrade) -> Dict[str, Dict[str, float]]:
    """The core's people by tile and trade less the people hired there; never below nothing."""
    return {tile: {trade: max(0.0, people - hires.get(tile, {}).get(trade, 0.0)) for trade, people in sorted(by_trade.items())}
            for tile, by_trade in sorted(core.items())}


def over_reserved(core: PeopleByTileAndTrade, hires: PeopleByTileAndTrade) -> List[Tuple[str, str, float, float]]:
    """(tile, trade, hired, held) wherever the hires at a tile in a trade exceed the people the core holds there."""
    found = []
    for tile, by_trade in sorted(hires.items()):
        for trade, hired in sorted(by_trade.items()):
            held = core.get(tile, {}).get(trade, 0.0)
            if hired > held + 1e-9:
                found.append((tile, trade, hired, held))
    return found


def reserved_hours_within_people(core: PeopleByTileAndTrade, hires: PeopleByTileAndTrade, hours_per_person: float) -> bool:
    """Whether the hours the hires reserve at every tile and trade are within the hours the core's people there give."""
    return all(hired * hours_per_person <= core.get(tile, {}).get(trade, 0.0) * hours_per_person + 1e-9
               for tile, by_trade in hires.items() for trade, hired in by_trade.items())
