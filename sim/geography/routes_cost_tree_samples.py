"""Sample calls of the `least_cost_tree` kernel, built in code: grids of tiles with several modes each, seeded costs, links within a
mode and changes of mode on a tile. The quick-tier rule test and a mod's equivalence check run the same ones."""
import random
from typing import List, Tuple

MODES = 3


def _grid(side: int, seed: int) -> list:
    """Per state of a side x side grid (tile * MODES + mode): (state reached, cost added) to the grid neighbours in the
    same mode and to the tile's other modes."""
    rng = random.Random(seed)
    adjacency = []
    for tile in range(side * side):
        row, column = divmod(tile, side)
        for mode in range(MODES):
            steps = []
            for next_row, next_column in ((row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)):
                if 0 <= next_row < side and 0 <= next_column < side and rng.random() < 0.85:
                    steps.append(((next_row * side + next_column) * MODES + mode, rng.uniform(0.2, 3.0) * (1 + mode)))
            steps.extend((tile * MODES + other, rng.uniform(0.05, 0.5)) for other in range(MODES) if other != mode)
            adjacency.append(tuple(steps))
    return adjacency


def samples() -> List[Tuple[tuple, dict]]:
    calls: List[Tuple[tuple, dict]] = []
    for side, seed, origin_tiles, settle in ((5, 1, (0,), None), (6, 2, (7, 20), None), (6, 3, (0,), {35, 30}), (7, 4, (24,), {0, 6, 48}),
                                              (4, 5, (3,), set()), (3, 6, (4,), {4})):
        adjacency = _grid(side, seed)
        starts = [(0.1 * (mode + 1), tile * MODES + mode) for tile in origin_tiles for mode in range(MODES)]
        calls.append(((adjacency, starts, MODES, None if settle is None else set(settle)), {}))
    return calls
