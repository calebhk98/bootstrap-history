"""Bridge entries the agriculture module uses until the modules that own these facts move.

Each view answers through `Sim` as the old mixin methods did; when its owner moves it publishes the same name and the entry
is deleted. The geography ones hand the module the per-tile sums over the held land. `legacy_dice` (the game's random
source) stays for the modules that have not moved to `game_random`."""
from sim.agriculture.api import SetFarmLand, SetFarmTechnique
from sim.world import agriculture as farm_rules

from .bridge import bridge_command, bridge_view


# ---- labour, prices, hazards and the game's own state ----

@bridge_view("legacy_dice")
def legacy_dice(sim):
    """The game's random source; the weather salt is drawn from it once."""
    return sim.rng


@bridge_command(SetFarmLand)
def set_farm_land(sim, command):
    """The farm's cleared ground, which the engine still holds as `sim.farm_land`."""
    sim.farm_land = farm_rules.Land(command.hectares, command.quality)


@bridge_command(SetFarmTechnique)
def set_farm_technique(sim, command):
    """The year's farming technique, which the engine still holds as `sim._farm_technique_this_year`."""
    sim._farm_technique_this_year = command.technique
