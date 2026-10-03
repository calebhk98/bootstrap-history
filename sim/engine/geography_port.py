"""The engine's side of the geography wall: what the geography package reads from the simulation, and
where the simulation keeps its `Geography`."""
from sim.geography.api import Geography


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


class GeographyPortMixin:
    """Gives `Sim` its geography as `sim.geography`. Not saved: it is rebuilt from the geography file."""

    @property
    def geography(self):
        geography = self.__dict__.get("_geography")
        if geography is None:
            geography = self.__dict__["_geography"] = Geography(GeographyWorld(self))
        return geography
