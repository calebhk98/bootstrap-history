"""People's moves between regions from both motives, as pairs (origin, destination, working-age people).

Food-driven pairs come from the labour package's migration rule over where people ate better (`migrant_pairs`); the labour
market's wage-driven moves arrive as a net change per tile (`MovePeople`) and are paired here. Both are applied together,
and no region sends more working-age people than it has."""
from typing import Dict, List, Mapping, Tuple

Pair = Tuple[str, str, float]


def pairs_of_net_moves(net_by_tile: Mapping[str, float], regions: Mapping[str, object]) -> List[Pair]:
    """Net changes (negative leaves a tile, positive arrives) as pairs: each leaving tile's people go to the arriving tiles
    in proportion to their gain. Tiles the nation does not track are ignored; what cannot be matched stays put."""
    leaving = {tile: -change for tile, change in sorted(net_by_tile.items()) if change < 0.0 and tile in regions}
    arriving = {tile: change for tile, change in sorted(net_by_tile.items()) if change > 0.0 and tile in regions}
    sent, received = sum(leaving.values()), sum(arriving.values())
    matched = min(sent, received)
    if matched <= 0.0:
        return []
    return [(origin, destination, people * matched / sent * gain / received)
            for origin, people in leaving.items() for destination, gain in arriving.items()]


def within_working_age(pairs: List[Pair], regions: Mapping[str, object]) -> List[Pair]:
    """`pairs` with each origin's moves scaled down together where they add up to more than its working-age people."""
    sent: Dict[str, float] = {}
    for origin, _destination, people in pairs:
        sent[origin] = sent.get(origin, 0.0) + people
    scale = {origin: min(1.0, regions[origin].working_age / total) if total > 0.0 else 1.0 for origin, total in sent.items()}
    return [(origin, destination, people * scale[origin]) for origin, destination, people in pairs]
