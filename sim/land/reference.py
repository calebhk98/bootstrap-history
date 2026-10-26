"""Views of the land that name no actor (where people live, what a colony can feed) use the default farming technique."""
from sim.geography.api import settlement
from sim.world import agriculture_tile, farming_technique


def install_reference_crop_technique() -> None:
	settlement.set_reference_crop_technique(agriculture_tile.crop_technique(farming_technique.DEFAULT_TECHNIQUE))
