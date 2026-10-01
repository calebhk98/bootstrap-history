"""The overview screens for the map, education, demography and divergence
(Complaints/243, 96, 270). Each reply is built by its own screen_* module."""

from .command_registry import command
from .screen_demography import demography_report
from .screen_divergence import divergence_report
from .screen_education import education_report
from .screen_map import map_report


@command("map", group="society", aliases=("geography", "country", "atlas"),
         summary="the land you hold: places, terrain, deposits, what is next door",
         usage=["map", "map full"], options={"full": "every tile, not the first dozen"},
         description="Your base, the tiles your nation holds by people and terrain, the "
                     "named deposits on each, the tiles bordering them, and the days to "
                     "reach each. Tile names are a country and a number; the data names "
                     "no towns.")
def _cmd_map(sim, nodes, cmd, ended):
    return {"ok": True, **map_report(sim, full=bool(cmd.get("full")))}


@command("education", group="society", aliases=("literacy", "schools", "schooling"),
         summary="literacy, schools and trainees",
         usage=["education"], options={},
         description="General and elite literacy against the ceiling each can reach and "
                     "what next year's schooling adds, the schools running and the flow "
                     "they give, printing's boost, the literate trades' pools and the "
                     "trainees in the pipeline.")
def _cmd_education(sim, nodes, cmd, ended):
    return education_report(sim)


@command("demography", group="society",
         summary="age cohorts, births, deaths, disease and food",
         usage=["demography"], options={},
         description="The three age cohorts, last year's births and deaths, the disease "
                     "burden, the nutrition ratio, epidemics under way and the people by "
                     "trade. Says what the model does not hold.")
def _cmd_demography(sim, nodes, cmd, ended):
    return demography_report(sim)


@command("divergence", group="society", aliases=("drift", "baseline"),
         summary="how far this run has left the recorded history",
         usage=["divergence"], options={},
         description="Start values against now (population, wages, prices, literacy, "
                     "territory), the technologies you built, and each dated event as "
                     "happened, under way or upcoming. Says what the game cannot know.")
def _cmd_divergence(sim, nodes, cmd, ended):
    return divergence_report(sim)
