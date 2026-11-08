"""The offered-price grid: every good's price on every tile, gathered from the market memory's table in one call."""
import numpy

from sim.jit import njit


@njit
def offered_by_good_tile(offered_by_market, market_of_good_tile):
    """Per (good row, tile row): the price a buyer can buy at (`market_table_kernels.offered_prices`, by market row) in the good's
    market on that tile. NaN means no price: the good has no market on the tile (-1 in `market_of_good_tile`), the memory has not
    numbered it, or nothing is on offer there. Never 0.0 for none."""
    goods, tiles = market_of_good_tile.shape
    grid = numpy.full((goods, tiles), numpy.nan)
    for good in range(goods):
        for tile in range(tiles):
            market = market_of_good_tile[good, tile]
            if 0 <= market < len(offered_by_market):
                grid[good, tile] = offered_by_market[market]
    return grid
