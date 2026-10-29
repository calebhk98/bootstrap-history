"""The scenario module: the civilisation the game is played in, the configuration it was built with, the modes it was set up in,
and the clock. Nothing else changes the year; the text helpers that follow the civilisation's coin and the player's units are
its views."""
import copy
from typing import Any, Dict, Optional, Set

from sim.assembly.api import Module

from . import constants, quantity_text, rules
from .commands import (AdvanceYear, OpenScenario, RecordOpeningLiteracy, ScenarioSources, SetEndYear, SetFog, SetFuzzyEstimates,
                       SetYear)

YEAR = "year"


class Scenario(Module):

	# set by OpenScenario (the game's inputs, which a save does not hold); the civilisation's data object is shared with the engine
	civilisation: Dict[str, Any]
	start_civilisation: Dict[str, Any]
	configuration: Dict[str, Any]
	manual: bool = False
	events: bool = True
	bounty_set: Set[str]
	sources: ScenarioSources
	end_year: Optional[int] = None

	# ---- commands ----

	def open_scenario(self, command: OpenScenario) -> None:
		self.civilisation = command.civilisation
		self.start_civilisation = copy.deepcopy(command.civilisation)   # the opening values, kept while the civilisation drifts
		self.configuration = command.configuration
		self.manual = bool(command.manual)
		self.events = command.events
		self.bounty_set = command.bounty_set
		self.sources = command.sources
		self.configuration["start_year"] = rules.opening_start_year(self.civilisation, self.configuration)

	def record_opening_literacy(self, command: RecordOpeningLiteracy) -> None:
		self.start_civilisation["literacy_general"] = command.general
		self.start_civilisation["literacy_elite"] = command.elite
		self.civilisation.pop("literacy_general", None)
		self.civilisation.pop("literacy_elite", None)

	def advance_year(self, command: AdvanceYear) -> int:
		self.world.year += 1
		self.bump(YEAR)
		return self.world.year

	def set_year(self, command: SetYear) -> None:
		self.world.year = command.year
		self.bump(YEAR)

	def set_fog(self, command: SetFog) -> None:
		self.world.fog = bool(command.on)

	def set_fuzzy_estimates(self, command: SetFuzzyEstimates) -> None:
		self.world.fuzzy_estimates = bool(command.on)
		if command.salt is not None:
			self.world.fuzzy_salt = command.salt

	def set_end_year(self, command: SetEndYear) -> None:
		self.end_year = command.year

	# ---- the clock and the modes ----

	def year(self) -> int:
		return self.world.year

	def fog(self) -> bool:
		"""Whether the game is played under fog of war (the mode of the game, set at its start)."""
		return self.world.fog

	def fuzzy_estimates(self) -> bool:
		"""Whether estimates are shown blurred (the mode of the game, set at its start or by the options screen)."""
		return self.world.fuzzy_estimates

	def fuzzy_salt(self) -> int:
		"""The salt of the blur; zero until the option has been turned on."""
		return self.world.fuzzy_salt

	def said_once(self) -> Set[str]:
		"""The set of notices the hazards and the levy have already told once (mutated in place: a debt)."""
		return self.world.said_condition

	def events_enabled(self) -> bool:
		"""Whether the game runs with its random events and hazards (a test or a replay may turn them off)."""
		return self.events

	def automation(self) -> Dict[str, Any]:
		return {"manual": self.manual, "bounty_set": self.bounty_set}

	# ---- the setup facts ----

	def civilisation_of_game(self) -> Dict[str, Any]:
		return self.civilisation

	def opening_civilisation(self) -> Dict[str, Any]:
		"""The civilisation as the game opened on it, before it drifted."""
		return self.start_civilisation

	def civilisation_record(self, civilization_id: str) -> Dict[str, Any]:
		"""The civilisation `civilization_id` as its file gives it (mods applied, checked)."""
		return self.sources.load_civilisation(civilization_id)

	def game_config(self) -> Dict[str, Any]:
		return self.configuration

	def game_setting(self, name: str) -> Any:
		return self.configuration[name]

	def start_year(self) -> int:
		return self.configuration["start_year"]

	def society_name(self) -> str:
		return rules.society_name(self.civilisation)

	def horizon_end_year(self) -> int:
		return rules.horizon_end_year(self.end_year, self.configuration)

	def danger_lines(self) -> Dict[str, Any]:
		return rules.danger_lines(self.configuration)

	def project_limits(self) -> Dict[str, Any]:
		return {"base": constants.MAX_ACTIVE_PROJECTS_BASE, "per_director_hours": constants.MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS,
		        "per_scholar": constants.MAX_ACTIVE_PROJECTS_PER_SCHOLAR, "per_artisan": constants.MAX_ACTIVE_PROJECTS_PER_ARTISAN}

	def founder_life_terms(self) -> Dict[str, Any]:
		return rules.founder_life_terms(self.configuration, constants.FOUNDER_MIN_REMAINING_LIFE_YEARS)

	def kit_capital(self, kit_id: str) -> float:
		"""A starting kit's money at the opening wage of this civilisation."""
		return self.sources.kit_capital(kit_id, self.civilisation)

	# ---- quantities in sentences: the units the player chose, the civilisation's coin ----

	def display(self) -> quantity_text.Display:
		registry, chosen, context = self.sources.display_units()
		return quantity_text.Display(self.civilisation, registry, chosen, context)

	def money_text(self, amount: float, grouped: bool = False, short: bool = False) -> str:
		return quantity_text.money_text(amount, self.display(), grouped=grouped, short=short)

	def mass_text(self, amount: float, digits: int = 0, grouped: bool = False, short: bool = False, unit: str = "tonne") -> str:
		return quantity_text.mass_text(amount, self.display(), digits=digits, grouped=grouped, short=short, unit=unit)

	def area_text(self, amount: float, digits: int = 0, grouped: bool = False, short: bool = False, unit: str = "hectare") -> str:
		return quantity_text.area_text(amount, self.display(), digits=digits, grouped=grouped, short=short, unit=unit)

	def mass_rate_text(self, amount: float, digits: int = 0, grouped: bool = False, short: bool = True, unit: str = "tonne") -> str:
		return quantity_text.mass_rate_text(amount, self.display(), digits=digits, grouped=grouped, short=short, unit=unit)

	def mass_per_area_text(self, tonnes_per_area: float, digits: int = 0, area: str = "square_metre") -> str:
		return quantity_text.mass_per_area_text(tonnes_per_area, self.display(), digits=digits, area=area)

	def plain_number(self, value: float, digits: int = 0) -> str:
		"""A count, a number of people or of hours, written for a sentence."""
		return quantity_text.plain_number(value, digits)
