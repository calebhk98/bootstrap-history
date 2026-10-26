"""The state campaigns owns: the armies and what they have taken from the land."""
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CampaignsWorld:
	armies: Dict[str, Dict[str, Any]] = field(default_factory=dict)   # army id -> the Army as a dict
	drawn: Dict[str, float] = field(default_factory=dict)             # tile -> food energy armies have taken from it this year
	held_since: Dict[str, Dict[str, Any]] = field(default_factory=dict)   # tile -> {year, by, from} for tiles taken by an army
	next_id: int = 1
