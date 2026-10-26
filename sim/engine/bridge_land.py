"""Bridge entries the land module reads until the owners behind them move into modules.

Each view asks the engine exactly as the old geography adapter did, and is never cached. `legacy_improvements` is the ways
built, which the ways code (ways.py) and the labour code still write and read in place on the economy state."""
import os

from sim.assembly.api import QUOTE

from .bridge import bridge_view
from .mods import get_ordered_mods

MODS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mods")


@bridge_view("map_overlays")
def map_overlays(sim):
    """[(mod id, directory)] of the installed mods, in load order: the map overlays the base map is merged with."""
    return [(manifest.id, manifest.directory) for manifest in get_ordered_mods(MODS_DIR)]


@bridge_view("legacy_improvements")
def legacy_improvements(sim):
    """The roads, track, canals, bridges and ports built, {edge key: {way: true}} (the live record)."""
    return sim.state.economy.improvements


@bridge_view("held_techniques", kind=QUOTE)
def held_techniques(sim, include_starting):
    """The techniques and results held and running, with the civilisation's starting ones or without."""
    return sim.held_and_running(include_starting)
