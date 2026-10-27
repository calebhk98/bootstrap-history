"""One-line forwarders from `Sim` to the agriculture module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself."""


class ForwardAgricultureMixin:

    def refresh_farm_territory(self):
        """The farm's ladder, ceiling and cleared ground's quality from the held tiles as they now are: the soil nitrogen
        stock and the society's rotation both move a tile's yield factor and cropped hectares. The ladder, the ceiling and
        the farm area are the farm workforce's, so they are set here until it moves."""
        territory = self.view("farm_territory")()
        self._farm_ladder = territory.ladder
        self._farm_arable_ceiling = territory.cropped_hectares
        self.labour.set_farm_area(self.farm_land.hectares)
