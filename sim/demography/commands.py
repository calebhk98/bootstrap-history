"""Commands to the owner of the people of each country."""
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from sim.assembly.api import Command


@dataclass(frozen=True)
class AddCaptives(Command):
	"""`people` taken in war join the bonded stratum of the country `winner`, where it has one. Answers the people added
	(zero where the country has no bonded stratum)."""
	winner: str
	people: float


@dataclass(frozen=True)
class CutPopulation(Command):
	"""The home society's age cohorts are cut unevenly (children and the elderly harder) so that the whole population falls
	by `share`."""
	share: float


@dataclass(frozen=True)
class RefreshDemographicIndexes(Command):
	"""The population and wage figures the screens show are recomputed for `year` now, not at year end."""
	year: int


@dataclass(frozen=True)
class KillPeople(Command):
	"""`share` of a country's people die (the home society by its age cohorts, a partner by its strata); the world event
	log records it with `cause`, its `kind`, the `tiles` and the `facts`. Answers the record, whose facts carry `died`."""
	country: str
	share: float
	cause: str
	kind: str = "deaths"
	tiles: Tuple[str, ...] = ()
	facts: Dict[str, Any] = field(default_factory=dict)
