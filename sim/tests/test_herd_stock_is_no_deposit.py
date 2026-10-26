"""Complaints/532: a herd good named like a catalogue herd animal (cattle_kg, cattle) is not a mined deposit."""
from .harness import *  # noqa: F401,F403

from sim.tests import resources_stand_in

QUICK_TOPIC = True


host = resources_stand_in.build()   # the mine lookup reads the world map and nothing else of the game
for material in ("cattle_kg", "sheep_kg", "goat_kg", "cattle", "sheep", "goat"):
    check("%s names no deposit resource" % material, host.mine_resource_id(material) is None,
          host.mine_resource_id(material))
    check("%s has no found deposits" % material, host.found_deposits(material) == [], None)
check("an ore still names its deposit resource",
      host.mine_resource_id("copper_ore_kg") is not None or host.mine_resource_id("copper") is not None, None)
check("a material no catalogue describes names none", host.mine_resource_id("zz_not_a_material_kg") is None)
