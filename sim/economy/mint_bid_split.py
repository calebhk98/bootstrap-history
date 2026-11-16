"""Where the mint's bid for its metal goes: to the market areas where the metal is, not to every area by its size."""
from typing import Dict


def split_bid(total: float, traded: Dict[str, float], tile_share: Dict[str, float]) -> Dict[str, float]:
    """`total` divided over the areas by the metal each traded last year (`traded`, by area). An area with none on
    record gets nothing while another has some; with no record in any area the bid follows `tile_share`."""
    record = sum(traded.values())
    weights = traded if record > 0.0 else tile_share
    weight_total = sum(weights.values())
    if weight_total <= 0.0:
        return {area: 0.0 for area in tile_share}
    return {area: total * weights.get(area, 0.0) / weight_total for area in tile_share}
