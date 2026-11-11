"""What the producers made last year in tonnes, the whole table by tile and good, as it was read before one good's
tonnes were read alone: plain reference code."""
from typing import Dict, Optional

from sim.markets.unit_mass import tonnes_per_unit


def tonnes_by_tile_and_good(output_by_tile: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    return {tile: {good: units * per_unit for good, units in row.items()
                   for per_unit in [tonnes_per_unit(good)] if per_unit is not None}
            for tile, row in {tile: dict(sorted(row.items())) for tile, row in sorted(output_by_tile.items())}.items()}


def output_tonnes_by_table(output_by_tile: Dict[str, Dict[str, float]], material: str, held: set) -> float:
    by_tile = tonnes_by_tile_and_good(output_by_tile)
    return sum(row.get(material, 0.0) for tile, row in by_tile.items() if tile in held)
