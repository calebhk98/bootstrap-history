"""What the disease step reads about the nation's people and the traffic between its tiles, from views."""
from sim.geography.api import settlement

from . import nation, nation_tuning as tuning, metapopulation as spread, rules


class People:

    def people_by_band(self):
        return dict(self.needs.people_by_band())

    def held_tiles(self):
        """The tiles the nation holds, sorted."""
        return sorted(self.needs.home_tiles_held())

    def people_by_tile(self):
        """{tile: {band: people}} over the tiles held (see `rules.people_by_tile`)."""
        held = self.held_tiles()
        return rules.people_by_tile(held, self.needs.regional_people_by_band(), settlement.tile_ids(held), tuning.BANDS,
                                    self.people_by_band(), lambda: settlement.population_shares(held))

    def area_by_tile(self):
        return {tile: self.needs.tile_description(tile)["land_area_km2"] for tile in self.held_tiles()}

    def crowding_index(self):
        """The person-weighted density of the nation relative to a rural settlement."""
        return nation.crowding_index(self.needs.urban_fraction(), tuning.DISEASE_URBAN_DENSITY_RATIO)

    def crowding_by_tile(self, people_by_tile):
        """{tile: crowding}: density over the people-weighted mean, times the nation's crowding index."""
        return spread.crowding_by_tile(people_by_tile, self.area_by_tile(), self.crowding_index())

    def trips(self, people_by_tile):
        """{(tile, tile): trips in a year} between the tiles: the crews of last year's carried goods, last year's
        migrants and the everyday travel between bordering tiles."""
        held = self.held_tiles()
        borders = self.needs.borders_among(held)
        local_borders = spread.borders_through_empty(people_by_tile, borders)
        carried = self.needs.goods_carried_last_year()
        flows = self.needs.regional_flows_last_year() or {}
        emigrants = {tile: flow.emigration for tile, flow in flows.items()}
        immigrants = {tile: flow.immigration for tile, flow in flows.items()}
        return spread.add_trips(spread.trade_trips(carried, held), spread.migrant_trips(emigrants, immigrants, borders),
                                spread.local_trips(people_by_tile, local_borders))

    def contacts(self, people_by_tile):
        return spread.contacts_from_trips(self.trips(people_by_tile), people_by_tile)

    def fatality_scale_by_band(self, nutrition_ratio):
        """Each band's multiplier on a pathogen's case fatality (see `nation.fatality_scale_by_band`)."""
        return nation.fatality_scale_by_band(self.people_by_band(), nutrition_ratio)
