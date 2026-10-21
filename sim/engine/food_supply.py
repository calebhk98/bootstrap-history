"""The food the held tiles give, bounded by the hours of the society's gatherers, and the game stock hunting draws.

`state.economy.wild_stock` is the saved {tile: {species: share of its carrying capacity left}} (geography's
food_wild_stock.py). Each year the hunters' hours bring in at most what the trade's return allows; that
much is taken from the held tiles' game, and the stock regrows. Fishers bound fishing the same way in
`society_food_potential`. Nothing here names a trade or a food source: both come from the trade registry.
The per-tile sums and the draw on the stock are sim/geography/food_society.py, reached as `self.geography`; this
mixin keeps the labour bound and hands geography the rotation, the crop technique and the soil factors.
"""
from sim.labour.api import cap_share, capped_kcal, hours_cap_kcal

from sim.world import agriculture_tile

from . import data


class FoodSupplyMixin:

    def _gathering_caps(self):
        """{food source id: kcal} the society's gatherers' hours allow this year."""
        registry = {trade_id: {"family": trade.family, **trade.extra} for trade_id, trade in data.TRADE_REGISTRY.items()}
        return hours_cap_kcal(self.state.economy.society_labour_hours, registry)

    def farm_sites(self):
        """{tile: geography's crop site} over the held tiles under the society's rotation."""
        technique = self.labour.farming_technique()
        share = 1.0 - technique.rotation.fallow_share_of_holding
        return self.geography.crop_sites(share, self.soil_nitrogen_factors(), technique.toolkit.tillage_capacity)

    def society_food_potential(self):
        """{source id: kcal a year} over the held tiles: the land's sustainable yield, game thinned by past hunting,
        each gathered source held to what the hours of its gatherers can bring in."""
        crop_technique = agriculture_tile.crop_technique(self.labour.farming_technique())
        totals = self.geography.food_kcal_by_source(
            self.state.economy.wild_stock, crop_technique, self.soil_nitrogen_factors())
        return capped_kcal(totals, self._gathering_caps())

    def step_wild_stock(self):
        """Hunters take what their hours allow from the held tiles' game, then the stock regrows a year."""
        economy = self.state.economy
        caps = self._gathering_caps()
        cap = sum(caps.get(source_id, 0.0) for source_id in self.geography.game_food_sources())
        stock = economy.wild_stock
        if cap > 0.0:
            available = self.geography.huntable_kcal(stock)
            share = cap_share(sum(sum(by_species.values()) for by_species in available.values()), cap)
            stock = self.geography.take_hunt(stock, available, share)
        economy.wild_stock = self.geography.regrow_wild_stock(stock) if stock else stock
