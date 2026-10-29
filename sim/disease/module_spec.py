"""The disease module's spec (sim/assembly).

Each read is a view of the module that owns the fact. The infection records are
saved in the world slot; the deaths by tile and the forecast are kept in the module and are empty after a load."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec
from sim.hazards.api import LoseCapital
from sim.reporting.api import RecordEvent
from sim.workforce.api import LoseStaff

from .commands import HitSeatsWithEpidemic, RunEpidemicYear
from .module import Disease
from .state import EPIDEMICS, DiseaseWorld

READS_BY_OWNER = {
    "core": ("year", "civilisation", "money_text"),
    "agriculture": ("weather_seed",),
    "demography": ("people_by_band", "nutrition_ratio", "working_age", "regional_people_by_band", "urban_fraction",
                   "regional_flows_last_year"),
    "land": ("home_tiles_held", "home_modes", "reach_days", "endemic_people_loss", "tile_description", "borders_among"),
    "freight": ("goods_carried_last_year",),
    "knowledge": ("techniques_held", "held_techniques"),
    "mechanics": ("effect_terms", "mechanic"),
    "diffusion": ("civ_diffusion", "tech_effects"),
    "coverage": ("coverage", "coverage_share"),
    "seats": ("seat_list",),
}

# The burden reads what is held and what coverage serves, written outside any command of theirs: never cached. The deaths
# by tile are written only by this module's run of the year, which bumps the channel.
MODULE_SPECS = (ModuleSpec(
    "disease", Disease, channels=(EPIDEMICS,), world_state=DiseaseWorld,
    publishes=(
        ViewSpec("disease_burden", "disease_burden", cached=False),
        ViewSpec("disease_burden_held", "disease_burden_held", kind=KEYED, cached=False),
        ViewSpec("disease_burden_weights", "disease_burden_weights", cached=False),
        ViewSpec("endemic_death_rates", "endemic_death_rates", cached=False),
        ViewSpec("epidemic_deaths_by_tile", "epidemic_deaths_by_tile", channels=(EPIDEMICS,)),
        ViewSpec("epidemic_forecast", "epidemic_forecast", kind=QUOTE),
        ViewSpec("epidemic_risk", "epidemic_risk", cached=False),
        ViewSpec("regional_disease_loss", "regional_disease_loss", kind=QUOTE),
        ViewSpec("frontier_disease_loss", "frontier_disease_loss", cached=False),
    ),
    applies=((RunEpidemicYear, "run_epidemic_year"), (HitSeatsWithEpidemic, "hit_seats")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(LoseStaff, LoseCapital, RecordEvent),
),)
