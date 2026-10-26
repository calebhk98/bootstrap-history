"""The food the held tiles give, bounded by the hours of the society's gatherers, and the game stock hunting draws.

`world.wild_stock` is the saved {tile: {species: share of its carrying capacity left}}. Each year the hunters' hours
bring in at most what the trade's return allows; that much is taken from the held tiles' game, and the stock regrows.
Fishers bound fishing the same way in `food_potential`. Nothing here names a trade or a food source: both come from
the trade registry. The per-tile sums are geography's, read as views; this keeps the labour bound."""
from sim.labour.api import cap_share, capped_kcal, hours_cap_kcal
from sim.world import agriculture_tile, land

WILD_STOCK = "wild_stock"   # the version channel of the wild stock


class Food:

    def _gathering_caps(self):
        """{food source id: kcal} the society's gatherers' hours allow this year."""
        return hours_cap_kcal(self.needs.society_labour_hours(), self.needs.trade_registry())

    def farm_sites(self):
        """{tile: geography's crop site} over the held tiles under the society's rotation."""
        technique = self.needs.farming_technique()
        share = 1.0 - technique.rotation.fallow_share_of_holding
        return self.needs.crop_sites(share, self.soil_nitrogen_factors(), technique.toolkit.tillage_capacity)

    def farm_territory(self):
        """The farm's ladder, ceiling and cleared ground's quality from the held tiles as they now are."""
        return land.territory_cropland(self.farm_sites())

    def food_potential(self):
        """{source id: kcal a year} over the held tiles: the land's sustainable yield, game thinned by past hunting, each
        gathered source held to what the hours of its gatherers can bring in."""
        crop_technique = agriculture_tile.crop_technique(self.needs.farming_technique())
        totals = self.needs.food_kcal_by_source(self.world.wild_stock, crop_technique, self.soil_nitrogen_factors())
        return capped_kcal(totals, self._gathering_caps())

    def wild_stock(self):
        return self.world.wild_stock

    def step_wild_stock(self, seats=None):
        """Hunters take what their hours allow from the held tiles' game, then the stock regrows a year."""
        caps = self._gathering_caps()
        cap = sum(caps.get(source_id, 0.0) for source_id in self.needs.game_food_sources())
        stock = self.world.wild_stock
        if cap > 0.0:
            available = self.needs.huntable_kcal(stock)
            share = cap_share(sum(sum(by_species.values()) for by_species in available.values()), cap)
            stock = self.needs.take_hunt(stock, available, share)
        self.world.wild_stock = self.needs.regrow_wild_stock(stock) if stock else stock
        self.bump(WILD_STOCK)
