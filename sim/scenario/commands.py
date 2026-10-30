"""The scenario module's commands: opening the game's setup, the clock, and the modes."""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Set

from sim.assembly.api import Command


@dataclass(frozen=True)
class ScenarioSources:
	"""What the game was built from and the options around it, which the scenario module reads but does not load: another
	civilisation's file, what a starting kit is worth in a civilisation's coin, and the unit registry with the unit the player
	chose per dimension and the numbers some units need (asked on each use: the options change and the numbers move)."""
	load_civilisation: Callable[[str], Dict[str, Any]]
	kit_capital: Callable[[str, Dict[str, Any]], float]   # (kit id, civilisation) -> money at the civilisation's opening wage
	display_units: Callable[[], Any]   # () -> (registry, {dimension: unit id}, () -> {number name: value})


@dataclass(frozen=True)
class OpenScenario(Command):
	"""Set the game up: the civilisation it is played in (the module keeps this object and a copy of its opening values), the
	configuration, whether the player chooses everything, whether random events run, the nodes the bounty policy posts for, and the
	game's one random source (every draw of a year comes from it; the save records its state). The civilisation's own date becomes
	the configuration's start year."""
	civilisation: Dict[str, Any]
	configuration: Dict[str, Any]
	manual: bool
	events: bool
	bounty_set: Set[str]
	sources: ScenarioSources
	dice: Any


@dataclass(frozen=True)
class RecordOpeningLiteracy(Command):
	"""The opening literacy of the civilisation, measured once its economy exists: kept as an opening value and taken out of the
	civilisation's own record."""
	general: float
	elite: float


@dataclass(frozen=True)
class AdvanceYear(Command):
	"""The year ends: the clock moves on one. Answers the new year."""


@dataclass(frozen=True)
class SetYear(Command):
	"""Put the clock at a year (the opening, a test, a replay)."""
	year: int


@dataclass(frozen=True)
class SetFog(Command):
	"""Play under fog of war or not."""
	on: bool


@dataclass(frozen=True)
class SetFuzzyEstimates(Command):
	"""Show estimates blurred or not; a salt, when given, replaces the blur's salt."""
	on: bool
	salt: Optional[int] = None


@dataclass(frozen=True)
class SetEndYear(Command):
	"""The year the player's horizon ends."""
	year: int
