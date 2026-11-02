"""What the economy keeps about land from year to year: the rent producers paid, who holds each tile and who rents it."""
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .record_parts import OwnedRecord
from .types import AgentId, TileId


@dataclass
class LandRecord(OwnedRecord):
    land_rent: Dict[TileId, float] = field(default_factory=dict)         # rent per hectare producers paid, by tile
    land_mean_value: Dict[TileId, float] = field(default_factory=dict)   # tile -> mean output value a hectare of the uses that set its rent (entrant_rent.py)
    land_ceded: Dict[TileId, float] = field(default_factory=dict)        # tile -> hectares let to producers that outbid the households' plots (land_priority.py)
    titles: Dict[TileId, Dict[AgentId, float]] = field(default_factory=dict)   # tile -> holder -> share of its land (titles.py)
    tenancies: Dict[TileId, List[Dict[str, Any]]] = field(default_factory=dict)   # tile -> rows of tenant, lessor, share, arrears
    cleared_hectares: Dict[TileId, float] = field(default_factory=dict)   # tile -> ground cleared and taken up, added to its cropland (titles_ground.py)

    AGENT_KEYED = ("titles",)
    SAVED_SORTED = ("titles", "tenancies", "cleared_hectares")
