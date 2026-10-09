"""The engine's side of the geography wall: what the geography package reads from the simulation, and
where the simulation keeps its `Geography`."""
import os

from sim.geography.api import Geography, open_map

from .data import load_civ
from .mods import get_ordered_mods

MODS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mods")


class GeographyWorld:
    """What one simulation's geography reads from it: the civilisation and its population scale."""

    def __init__(self, sim):
        self._sim = sim

    @property
    def civ(self):
        return self._sim.civ

    @property
    def pop_scale(self):
        return self._sim.pop_scale

    @property
    def world_map(self):
        return self._sim.world_map

    @property
    def held_nodes(self):
        """The technologies the civilisation holds and keeps in service, and what its actions returned."""
        return self._sim.held_and_running()

    @property
    def improvements(self):
        """The roads and track built, {edge key: {way: true}}."""
        return self._sim.state.economy.improvements

    def civilisation(self, civilisation_id):
        """A civilisation's record, or None when there is none by that id."""
        try:
            return load_civ(civilisation_id)
        except (OSError, ValueError, KeyError):
            return None


class GeographyPortMixin:
    """Gives `Sim` its geography as `sim.geography` and its map as `sim.world_map`. Not saved: both are rebuilt
    from the map files and the installed mods."""

    @property
    def world_map(self):
        """The base map with every installed mod's map overlay merged, in the mods' load order."""
        world_map = self.__dict__.get("_world_map")
        if world_map is None:
            world_map = self.__dict__["_world_map"] = open_map(
                [(manifest.id, manifest.directory) for manifest in get_ordered_mods(MODS_DIR)])
        return world_map

    @property
    def geography(self):
        geography = self.__dict__.get("_geography")
        if geography is None:
            geography = self.__dict__["_geography"] = Geography(GeographyWorld(self))
        return geography
