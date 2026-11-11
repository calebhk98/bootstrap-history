"""The outside option of a tenant by comparing every pair of tiles, and the names of the markets of the labour offers a name at a time:
what `land_lease_year._outside_options` and `LabourIds.market_names` did before they were read in blocks."""
from sim.economy import land_tenancy


def plain_outside_options(margins, posted, labour_area):
    options = {}
    for tile in margins:
        options[tile] = land_tenancy.outside_option(
            [margin - posted.get(other, 0.0) for other, (margin, _recipe) in margins.items()
             if other != tile and labour_area(other) == labour_area(tile)])
    return options


def plain_market_names(ids, market_trades, market_areas):
    return [(ids.trades.name(trade), ids.areas.name(area)) for trade, area in zip(market_trades.tolist(), market_areas.tolist())]
