"""The state the land module owns: who holds each tile, the ways and works built, and each seat's colonies."""
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class LandWorld:
	# tile -> {owner: country or seat id}, seeded from the civilisation files on first use (ownership.py)
	tile_owners: Dict[str, Dict[str, str]] = field(default_factory=dict)
	# claims the seeding refused because another civilisation file already held the tile: {tile, owner, claimant}
	tile_claim_conflicts: List[Dict[str, Any]] = field(default_factory=list)
	# edge key (a port: tile id) -> {way: true} of the roads, track, canals, bridges and ports built; geography's routes read it
	improvements: Dict[str, Dict[str, bool]] = field(default_factory=dict)
	# the same key -> {way: {due year, crew trade and hours a year, engineered, year last pressed}} of the ways paid for and being built
	ways_under_construction: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)
	# tile -> {construction node id: capacity built there}
	works: Dict[str, Dict[str, float]] = field(default_factory=dict)
	# tile -> {construction node id: [year it is finished, capacity]} of works paid for and being built
	works_under_construction: Dict[str, Dict[str, List[float]]] = field(default_factory=dict)


@dataclass
class LandSeat:
	# settlements the seat has founded on tiles beyond its country's own: tile, year founded, by, and the three age cohorts
	colonies: List[Dict[str, Any]] = field(default_factory=list)
