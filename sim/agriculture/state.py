"""The state the agriculture module owns."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AgricultureWorld:
    # tile -> {species id: share of the game left} for hunted species below a full stock
    wild_stock: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # tile -> share of its native soil nitrogen pool left, for cropped tiles below native
    soil_nitrogen: Dict[str, float] = field(default_factory=dict)
    # this game's own weather history, drawn once from the game's dice at the first weather seed (Complaint 384)
    weather_salt: int = 0
