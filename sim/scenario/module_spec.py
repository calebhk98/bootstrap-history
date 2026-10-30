"""The scenario module's spec (sim/assembly).

It owns the clock, the modes (fog, fuzzy estimates) and the facts of the game's setup, and publishes the text helpers that
follow the civilisation's coin and the player's units. It reads no view: the data it was built from (another civilisation's
file, what a kit is worth, the unit registry and the player's units) reaches it through the `OpenScenario` command, so every
other module can read it without a cycle."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec

from .commands import (AdvanceYear, OpenScenario, RecordOpeningLiteracy, SetEndYear, SetFog, SetFuzzyEstimates, SetYear)
from .module import YEAR, Scenario
from .state import ScenarioWorld

# not cached: the configuration and the civilisation are shared objects the engine and the front ends still change in place
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
	"scenario", Scenario, channels=(YEAR,), world_state=ScenarioWorld,
	publishes=(
		ViewSpec("year", "year", channels=(YEAR,)),
		ViewSpec("fog_of_war", "fog_of_war", **_LIVE),
		ViewSpec("legacy_fuzzy_estimates", "fuzzy_estimates", **_LIVE),
		ViewSpec("fuzzy_salt", "fuzzy_salt", **_LIVE),
		ViewSpec("events_enabled", "events_enabled", **_LIVE),
		ViewSpec("automation", "automation", **_LIVE),
		ViewSpec("civilisation", "civilisation_of_game", **_LIVE),
		ViewSpec("game_random", "game_random", **_LIVE),
		ViewSpec("civilisation_record", "civilisation_record", kind=KEYED, **_LIVE),
		ViewSpec("opening_civilisation", "opening_civilisation", **_LIVE),
		ViewSpec("game_config", "game_config", **_LIVE),
		ViewSpec("game_setting", "game_setting", kind=KEYED, **_LIVE),
		ViewSpec("start_year", "start_year", **_LIVE),
		ViewSpec("society_name", "society_name", **_LIVE),
		ViewSpec("horizon_end_year", "horizon_end_year", **_LIVE),
		ViewSpec("danger_lines", "danger_lines", **_LIVE),
		ViewSpec("project_limits", "project_limits", **_LIVE),
		ViewSpec("founder_life_terms", "founder_life_terms", **_LIVE),
		ViewSpec("kit_capital", "kit_capital", kind=QUOTE),
		ViewSpec("money_text", "money_text", kind=QUOTE),
		ViewSpec("mass_text", "mass_text", kind=QUOTE),
		ViewSpec("area_text", "area_text", kind=QUOTE),
		ViewSpec("mass_rate_text", "mass_rate_text", kind=QUOTE),
		ViewSpec("mass_per_area_text", "mass_per_area_text", kind=QUOTE),
		ViewSpec("plain_number", "plain_number", kind=QUOTE),
	),
	applies=((OpenScenario, "open_scenario"), (RecordOpeningLiteracy, "record_opening_literacy"), (AdvanceYear, "advance_year"),
	         (SetYear, "set_year"), (SetFog, "set_fog"), (SetFuzzyEstimates, "set_fuzzy_estimates"), (SetEndYear, "set_end_year")),
),)
