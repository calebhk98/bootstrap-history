"""Commands to the owner of the people of each country."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

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


@dataclass(frozen=True)
class OpenPopulation(Command):
    """The nation's people are set to the age structure its civilisation's size settles into when fed exactly at need (the
    opening of a game)."""


@dataclass(frozen=True)
class StepPopulation(Command):
    """The yearly step of `year`: the farm year (the farm workforce, the harvest, the granary), then each region's people fed
    and stepped, the colonies, and the wage note. Answers None."""
    year: int


@dataclass(frozen=True)
class RecordFoodEaten(Command):
    """What the economy's year closed with: the nation's people-weighted food eaten over need (None when no cohort had a
    hunger need) and each tile's, kept for the next yearly step."""
    national: Optional[float]
    by_tile: Dict[str, float]


@dataclass(frozen=True)
class SendSettlers(Command):
    """`people` of working age leave the home people for a colony."""
    people: float


@dataclass(frozen=True)
class NotePopulationChange(Command):
    """The change in the nation's people over the year just played (a share), kept for the screens."""
    change: float


@dataclass(frozen=True)
class ChangeFarmland(Command):
    """The acting seat's farmland changes by `hectares` (bought positive, sold negative). Answers the hectares held."""
    hectares: float


@dataclass(frozen=True)
class SetClearedFarmland(Command):
    """The acting seat records `hectares` as the area its farm has cleared."""
    hectares: float


@dataclass(frozen=True)
class SetFarmHoursNeeded(Command):
    """The acting seat records `hours` as the labour hours its farm needs in a year."""
    hours: float


@dataclass(frozen=True)
class TakeFromGranary(Command):
    """`kilograms` of grain leave the acting seat's granary, never taking it below nothing."""
    kilograms: float
