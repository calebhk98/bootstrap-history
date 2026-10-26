"""The state the land module owns: who holds each tile, and each seat's colonies."""
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class LandWorld:
	# tile -> {owner: country or seat id}, seeded from the civilisation files on first use (ownership.py)
	tile_owners: Dict[str, Dict[str, str]] = field(default_factory=dict)
	# claims the seeding refused because another civilisation file already held the tile: {tile, owner, claimant}
	tile_claim_conflicts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class LandSeat:
	# settlements the seat has founded on tiles beyond its country's own: tile, year founded, by, and the three age cohorts
	colonies: List[Dict[str, Any]] = field(default_factory=list)
