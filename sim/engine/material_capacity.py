"""What a society can bring to market of a material, from what physically exists.

A mined material is bounded by the deposits on the tiles held (each deposit's working rate, never more than
it has left) and a made material by the plants of the producers that make it. Nothing here reads a price.
"""
from typing import Any, Iterable, Mapping

from sim.constants import declare

DEFAULT_MARKET_SHARE_OF_CAPACITY = declare(
    "DEFAULT_MARKET_SHARE_OF_CAPACITY", 1.0, kind="temporary_heuristic",
    unit="fraction of the society's capacity", source=None, confidence="D",
    why="Producers and mines of a material nobody has studied sell to whoever pays, so an ordinary buyer's reach "
        "is bounded by the standing ceiling (`MARKET_STANDING_SHARE_CEILING`), not by a share fitted to price. "
        "It goes when bulk and transport limits are stated per material.")


def mined_capacity_tonnes(deposit_rows: Iterable[Mapping[str, Any]]) -> float:
    """Tonnes a year the found deposits can yield: each one's working rate (already capped at what is left in it)."""
    return sum(float(row.get("rate_tonnes_per_year") or 0.0) for row in deposit_rows)


def producer_capacity_tonnes(producers: Iterable[Any], recipes: Mapping[str, Any], material: str,
                             tonnes_per_unit: float) -> float:
    """Tonnes a year the producers' plants allow of `material`: runs a year times what a run makes of it."""
    units = 0.0
    for producer in producers:
        recipe = recipes.get(producer.recipe_id)
        if recipe is not None:
            units += producer.capacity_runs * recipe.outputs.get(material, 0.0)
    return units * tonnes_per_unit
