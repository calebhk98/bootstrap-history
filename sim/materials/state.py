"""The state the materials module owns: one seat's shortage readings."""
import collections
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class MaterialsSeat:
    shortages: collections.Counter = field(default_factory=collections.Counter)   # pool -> readings in which it bound the pace
    throttle: float = 1.0                                   # the share of planned work the last reading let run
    binding: Optional[str] = None                           # the pool that bound it, or None
    shortage_condition: Optional[Dict[str, Any]] = None     # the standing shortage the player was told of: material, since, reported, previous, latest
    # tonnes a year per material the last throttle saw; the next year's prices read it before it is recomputed
    material_demand_at_last_throttle: Optional[Dict[str, float]] = None
