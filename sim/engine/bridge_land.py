"""Bridge entries the land module reads until the owners behind them move into modules.

Each view asks the engine exactly as the old geography adapter did, and is never cached."""
import os

from .bridge import bridge_view
from .mods import get_ordered_mods

MODS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mods")


@bridge_view("map_overlays")
def map_overlays(sim):
    """[(mod id, directory)] of the installed mods, in load order: the map overlays the base map is merged with."""
    return [(manifest.id, manifest.directory) for manifest in get_ordered_mods(MODS_DIR)]
