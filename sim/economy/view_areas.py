"""The market areas of many goods on one tile, from any market view (the real one answers in a block; a stand-in answers one by one)."""
from typing import List, Sequence


def areas_in(view, names: Sequence[str], tile: str) -> List[str]:
    """`view.area_of(name, tile)` for each name, through the view's `areas_of` when it has one."""
    block = getattr(view, "areas_of", None)
    return block(names, tile) if block is not None else [view.area_of(name, tile) for name in names]
