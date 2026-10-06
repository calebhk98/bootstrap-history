"""The map's own data checks, for `simulator.py validate`."""
from sim.engine.ui_port import MODDIR, get_ordered_mods
from sim.geography.api import open_map, problems


def map_problems():
    """The base map merged with the installed mods' overlays, as `geography.problems()` messages."""
    mods = [(manifest.id, manifest.directory) for manifest in get_ordered_mods(MODDIR)]
    return ["map: " + message for message in problems(open_map(mods))]
