"""Demography's module spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_demography.py and
the other bridge files) under the name the owner will publish, or one an owner that moved publishes. No view but the
reference population is cached: the
people's are three floats, which cost less to build than a signature to check, and the rest read the held land, the labour
market and the built ways, all written outside any command of this module."""
from sim.actors.api import RecordMigrantContact, ScaleStrata
from sim.assembly.api import QUOTE, ModuleSpec, ViewSpec
from sim.disease.api import HitSeatsWithEpidemic, RunEpidemicYear
from sim.hazards.api import RecordWorldEvent
from sim.land.api import AdvanceColonies
from sim.reporting.api import RecordEvent
from sim.workforce.api import AllocateFarmWorkforce, ApplyLandClearing, UpdateWages

from .commands import (AddCaptives, ChangeFarmland, CutPopulation, KillPeople, NotePopulationChange, OpenPopulation,
                       RecordFoodEaten, RefreshDemographicIndexes, SendSettlers, SetClearedFarmland, SetFarmHoursNeeded,
                       StepPopulation, TakeFromGranary)
from .module import Demography
from .state import DemographySeat, DemographyWorld

READS_BY_OWNER = {
    "core": ("civilisation", "year", "legacy_actor_registry"),
    "land": ("home_tiles_held", "borders_among", "built_ways", "held_techniques"),
    "disease": ("disease_burden", "endemic_death_rates", "epidemic_deaths_by_tile"),
    "hazards (externalities)": ("externality_deaths",),
    "workforce": ("farming_technique", "town_mortality_premium_by_tile", "wage_index", "wage_index_terms"),
    "defence_stores": ("relief_kcal_per_day",),
    "agriculture": ("weather_seed", "harvest_weather", "farm_land", "farm_technique_this_year"),
    "hazards": ("country_strata",),
}

_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "demography", Demography, world_state=DemographyWorld, seat_state=DemographySeat,
    publishes=(
        ViewSpec("population", "population", **_LIVE),
        ViewSpec("population_total", "population_total", **_LIVE),
        ViewSpec("working_age", "working_age", **_LIVE),
        ViewSpec("pop_scale", "pop_scale", **_LIVE),
        ViewSpec("default_population", "default_population"),
        ViewSpec("population_change_last_year", "population_change_last_year", **_LIVE),
        ViewSpec("yearly_record", "yearly_record", **_LIVE),
        ViewSpec("people_by_tile", "people_by_tile", **_LIVE),
        ViewSpec("people_by_band", "people_by_band", **_LIVE),
        ViewSpec("nutrition_ratio", "nutrition_ratio", kind=QUOTE),
        ViewSpec("legacy_regions_of_people", "legacy_regions_of_people", **_LIVE),
        ViewSpec("urban_people_by_tile", "urban_people_by_tile", **_LIVE),
        ViewSpec("urban_ceilings", "urban_ceilings", **_LIVE),
        ViewSpec("urban_fraction", "urban_fraction", **_LIVE),
        ViewSpec("food_eaten", "food_eaten", **_LIVE),
        ViewSpec("demographic_flows", "demographic_flows", **_LIVE),
        ViewSpec("regional_flows_last_year", "regional_flows_last_year", **_LIVE),
        ViewSpec("farm_holdings", "farm_holdings", seat_scoped=True, **_LIVE),
    ),
    applies=((AddCaptives, "add_captives"), (CutPopulation, "cut_population"), (KillPeople, "kill_people"),
             (RefreshDemographicIndexes, "refresh_demographic_indexes"), (OpenPopulation, "open_population"),
             (StepPopulation, "step_population"), (RecordFoodEaten, "record_food_eaten"), (SendSettlers, "send_settlers"),
             (NotePopulationChange, "note_population_change"), (ChangeFarmland, "change_farmland"),
             (SetClearedFarmland, "set_cleared_farmland"), (SetFarmHoursNeeded, "set_farm_hours_needed"),
             (TakeFromGranary, "take_from_granary")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(AdvanceColonies, AllocateFarmWorkforce, ApplyLandClearing, HitSeatsWithEpidemic, RecordEvent, RecordMigrantContact,
           RecordWorldEvent, RunEpidemicYear, ScaleStrata, UpdateWages),
),)
