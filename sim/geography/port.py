"""The geography package's port: what outside code asks about where things are and what reach costs."""


class GeographyPort:
    """Questions about the geography of one simulation (`sim.geography`)."""

    def __init__(self, sim):
        self._sim = sim

    def open(self, geo):
        """Set the simulation's geography up from the loaded geography file, once, at its start."""
        self._sim._open_geography(geo)

    @property
    def data(self):
        """The raw geography file's contents."""
        return self._sim.geo

    @property
    def regions(self):
        """Every region's record, by region id."""
        return self._sim._regions

    @property
    def home_centroid(self):
        """(latitude, longitude) averaged over the civilisation's home regions."""
        return self._sim._home_centroid

    def region_reach(self, region_id):
        return self._sim.region_reach(region_id)

    def material_reach(self, material_key):
        return self._sim.material_reach(material_key)

    def material_cost_factor(self, node_id):
        return self._sim.material_cost_factor(node_id)

    def mineral_scale(self, material):
        return self._sim.mineral_scale(material)
