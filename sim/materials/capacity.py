"""What a society can bring to market of a material, from what physically exists.

A mined material is bounded by the deposits on the tiles held (each deposit's working rate, never more than
it has left) and a made material by the plants of the producers that make it. Nothing here reads a price.
"""
import operator
from typing import Any, Callable, Dict, Iterable, List, Mapping

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


def producer_units_by_material(producers: Iterable[Any], recipes: Mapping[str, Any]) -> Dict[str, float]:
    """Units a year of every material the producers' plants allow, in one pass; each material's total adds the
    producers in the order given, as `producer_capacity_tonnes` does."""
    units: Dict[str, float] = {}
    for producer in producers:
        recipe = recipes.get(producer.recipe_id)
        if recipe is not None:
            for material, quantity in recipe.outputs.items():
                units[material] = units.get(material, 0.0) + producer.capacity_runs * quantity
    return units


class ProducerCapacityCache:
    """`producer_units_by_material` kept while the producers are the very same objects. A producer is
    immutable and a change replaces it, so the same objects in the same order are the same capacity."""

    def __init__(self) -> None:
        self._owner: Any = None
        self._recipes: Any = None
        self._seen: List[Any] = []
        self._units: Dict[str, float] = {}

    def units_by_material(self, owner: Any, all_producers: Iterable[Any],
                          scoped_producers: Callable[[], Iterable[Any]],
                          recipes: Mapping[str, Any]) -> Dict[str, float]:
        """`all_producers` is what the owner holds (cheap to list); `scoped_producers()` is the subset this
        reading counts, which depends only on the owner and on that list, and is built on a change only."""
        current = list(all_producers)
        if (owner is not self._owner or recipes is not self._recipes or len(current) != len(self._seen)
                or not all(map(operator.is_, current, self._seen))):
            self._owner, self._recipes, self._seen = owner, recipes, current
            self._units = producer_units_by_material(scoped_producers(), recipes)
        return self._units
