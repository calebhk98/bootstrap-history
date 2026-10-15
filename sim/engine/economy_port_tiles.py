"""What the economy answers for one tile: the prices its buyers and sellers face and what the sellers there hold.

Part of the port. Money is counted in coin here, the engine's unit; quantities in tonnes. Everything is read through
`sim.economy.api`, and kept until the economy's answers for the year are rebuilt."""
from sim.economy import api as economy_api

from .material_units import tonnes_per_unit


class TilePricesMixin:
    """Mixin of `AgentEconomy`: reads of the economy's prices on a tile."""

    def _tile_in_economy(self, tile):
        """The tile asked about, or the capital when the economy does not hold it."""
        setup = self.economy().setup
        return tile if tile in setup.tiles else setup.capital_tile

    def port_tile(self):
        """The tile where cargo enters and leaves the economy."""
        return self.economy().setup.port_tile

    def prices_at(self, tile):
        """{good: money per unit} on the tile in coin; the same dict while the year's answers stand."""
        answers = self.answers()
        tile = self._tile_in_economy(tile)
        held = getattr(self, "_tile_prices", None)
        if held is None or held[0] is not answers:
            held = self._tile_prices = (answers, {})
        if tile not in held[1]:
            coin = self._economy.setup.coin_per_unit
            prices, _stale = economy_api.prices_at(self._economy, tile)
            held[1][tile] = {good: price * coin for good, price in prices.items()}
        return held[1][tile]

    def offered_tonnes(self, material, tile):
        """Tonnes the sellers of a material in the tile's market area held at the last clearing; None when the area
        has no book for it."""
        per_unit = tonnes_per_unit(material)
        economy = self.economy()
        if not per_unit or per_unit <= 0.0 or material not in economy.area_map.goods():
            return None
        units = economy_api.offered_units(economy, material, self._tile_in_economy(tile))
        return None if units is None else units * per_unit
