"""The market areas of many goods on one tile, from any market view (the real one answers in a block; a stand-in answers one by one)."""
from typing import List, Sequence


def areas_in(view, names: Sequence[str], tile: str) -> List[str]:
    """`view.area_of(name, tile)` for each name, through the view's `areas_of` when it has one."""
    block = getattr(view, "areas_of", None)
    return block(names, tile) if block is not None else [view.area_of(name, tile) for name in names]


def areas_of_pairs(view, names: Sequence[str], tiles: Sequence[str]) -> List[str]:
    """`view.area_of(names[i], tiles[i])` for each pair in order, the view asked once for each distinct tile."""
    positions_on = {}
    for position, tile in enumerate(tiles):
        positions_on.setdefault(tile, []).append(position)
    found = [None] * len(names)
    for tile, positions in positions_on.items():
        for position, area in zip(positions, areas_in(view, [names[each] for each in positions], tile)):
            found[position] = area
    return found
