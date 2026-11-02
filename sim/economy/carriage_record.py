"""What the economy keeps about carriage from year to year: the ways the market areas are partitioned for, and what was carried."""
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .record_parts import OwnedRecord


@dataclass
class CarriageRecord(OwnedRecord):
    ways: Dict[str, Dict[str, Any]] = field(default_factory=dict)        # the built ways the market areas are partitioned for
    area_imbalance: float = 1.0                                          # the return-trip emptiness the market areas were partitioned for (its memory is keyed by those areas)
    carried: Dict[str, Dict[str, float]] = field(default_factory=dict)   # tonnes the merchants carried last year: origin tile -> destination tile (sim.geography.flow_ledger)
    carried_goods: Dict[str, Dict[str, Dict[str, List[float]]]] = field(default_factory=dict)   # the same flows by good: good -> origin -> destination -> [tonnes, value at origin's price, value at destination's price] (carried_book.py)

    SAVED_SORTED = ("ways", "carried")
