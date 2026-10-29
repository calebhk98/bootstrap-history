"""Bridge entries the agriculture module uses until the modules that own these facts move.

Each view answers through `Sim` as the old mixin methods did; when its owner moves it publishes the same name and the entry
is deleted. The geography ones hand the module the per-tile sums over the held land."""
from sim.agriculture.api import SetFarmLand, SetFarmTechnique
from sim.world import agriculture as farm_rules

from .bridge import bridge_command, bridge_view


# ---- labour, prices, hazards and the game's own state ----

@bridge_command(SetFarmLand)
def set_farm_land(sim, command):
    """The farm's cleared ground, which the engine still holds as `sim.farm_land`."""
    sim.farm_land = farm_rules.Land(command.hectares, command.quality)


@bridge_command(SetFarmTechnique)
def set_farm_technique(sim, command):
    """The year's farming technique, which the engine still holds as `sim._farm_technique_this_year`."""
    sim._farm_technique_this_year = command.technique
