"""The food the held tiles give, bounded by the hours of the society's gatherers, and the game stock hunting draws.

`state.economy.wild_stock` is the saved {tile: {species: share of its carrying capacity left}} (geography's
food_wild_stock.py). Each year the hunters' hours bring in at most what the trade's return allows; that
much is taken from the held tiles' game, and the stock regrows. Fishers bound fishing the same way in
`society_food_potential`. Nothing here names a trade or a food source: both come from the trade registry.
"""
from sim.geography.api import (draw_wild_stock, food_potential, game_food_sources, hunted_kcal, regrow_wild_stock,
                               tiles_held)
from sim.labour.api import cap_share, capped_kcal, hours_cap_kcal

from . import data


class FoodSupplyMixin:

    def _gathering_caps(self):
        """{food source id: kcal} the society's gatherers' hours allow this year."""
        registry = {trade_id: {"family": trade.family, **trade.extra} for trade_id, trade in data.TRADE_REGISTRY.items()}
        return hours_cap_kcal(self.state.economy.society_labour_hours, registry)

    def society_food_potential(self):
        """{source id: kcal a year} over the held tiles: the land's sustainable yield, game thinned by past hunting,
        each gathered source held to what the hours of its gatherers can bring in."""
        stock = self.state.economy.wild_stock
        totals = {}
        for tile_id in tiles_held(self.civ, self.world_map):
            for source_id, kcal in food_potential(
                    tile_id, None, self.world_map, stock)["kcal_per_year"].items():
                totals[source_id] = totals.get(source_id, 0.0) + kcal
        return capped_kcal(totals, self._gathering_caps())

    def step_wild_stock(self):
        """Hunters take what their hours allow from the held tiles' game, then the stock regrows a year."""
        economy = self.state.economy
        caps = self._gathering_caps()
        cap = sum(caps.get(source_id, 0.0) for source_id in game_food_sources(self.world_map))
        stock = economy.wild_stock
        if cap > 0.0:
            tiles = tiles_held(self.civ, self.world_map)
            available = {tile_id: hunted_kcal(tile_id, stock, self.world_map) for tile_id in tiles}
            share = cap_share(sum(sum(by_species.values()) for by_species in available.values()), cap)
            for tile_id, by_species in available.items():
                stock = draw_wild_stock(
                    stock, tile_id, {species: kcal * share for species, kcal in by_species.items()}, self.world_map)
        economy.wild_stock = regrow_wild_stock(stock, self.world_map) if stock else stock
