"""Complaints/532: a herd good named like a catalogue herd animal (cattle_kg, cattle) is not a mined deposit."""
from .harness import *  # noqa: F401,F403

founder = sim(civ="rome_100ad", capital=1e6)
for material in ("cattle_kg", "sheep_kg", "goat_kg"):
    check("%s names no deposit resource" % material, founder.mine_resource_id(material) is None,
          founder.mine_resource_id(material))
    check("%s has no found deposits" % material, founder.found_deposits(material) == [], None)
check("an ore still names its deposit resource", founder.mine_resource_id("copper_ore_kg") is not None
      or founder.mine_resource_id("copper") is not None, None)
check("the market output of a herd good is a number, not a map error",
      founder._national_output_tonnes("cattle_kg") >= 0.0, None)
