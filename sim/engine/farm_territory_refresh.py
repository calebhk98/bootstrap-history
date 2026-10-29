"""Keeping the farm workforce's ladder, ceiling and cleared area in step with the held tiles."""
from sim.agriculture.api import SetFarmTerritory


def refresh_farm_territory(sim):
    """The farm's ladder, ceiling and cleared ground's quality from the held tiles as they now are: the soil nitrogen
    stock and the society's rotation both move a tile's yield factor and cropped hectares. The ladder, the ceiling and
    the farm area are the farm workforce's, so they are set here until it moves."""
    territory = sim.view("farm_territory")()
    sim.send(SetFarmTerritory(territory.ladder, territory.cropped_hectares))
    sim.labour.set_farm_area(sim.view("farm_land")().hectares)
