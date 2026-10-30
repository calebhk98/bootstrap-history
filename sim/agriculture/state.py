"""The state the agriculture module owns."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sim.world import farming_technique


@dataclass
class AgricultureWorld:
    # tile -> {species id: share of the game left} for hunted species below a full stock
    wild_stock: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # tile -> share of its native soil nitrogen pool left, for cropped tiles below native
    soil_nitrogen: Dict[str, float] = field(default_factory=dict)
    # this game's own weather history, drawn once from the game's dice at the first weather seed (Complaint 384)
    weather_salt: int = 0
    # the farm's cleared ground and the yield of the best-first ground it covers
    cleared_hectares: float = 0.0
    cleared_quality: float = 1.0
    # [(yield factor, cropped hectares)], best ground first, and the cropland ceiling, from the held tiles; None until opened
    ladder: List[Tuple[float, float]] = field(default_factory=list)
    arable_ceiling: Optional[float] = None
    # the area the opening cleared, an initial condition; None until the farm opens
    opening_farmed_hectares: Optional[float] = None
    # the year's chosen technique: not saved (the `alias` mark skips a field), so a loaded game starts on the default
    # until the workforce chooses
    technique_this_year: Any = field(default=farming_technique.DEFAULT_TECHNIQUE, metadata={"alias": True})
