"""Bonded purchase between the agents' strata and the economy's labour market (Complaint 644): which tiles allow it,
who is for sale there, and paying the owners for the people the labour core bought."""
from sim.agents import api as agents_api


def bondage_tiles(sim, economy):
    """The economy's tiles in countries that recognise bondage."""
    return tuple(tile for tile in agents_api.bondage_tiles(sim.view("cast")()) if tile in economy.setup.tiles)


def bonded_for_sale(sim, economy):
    """{tile: {trade: people}} the bonded strata offer, on the economy's tiles."""
    return {tile: by_trade for tile, by_trade in agents_api.bonded_for_sale(sim.view("cast")()).items()
            if tile in economy.setup.tiles}


def settle_purchases(sim, economy, outcome):
    """Move the people the economy bought out of the bonded strata of the tiles they were bought on and pay, over the
    exchange edge (in coin), their owners the ask and the merchants the carriage. Returns the people moved."""
    buyer = sim.view("legacy_edge_account")[agents_api.edges.EDGE_ECONOMY]
    coin = economy.setup.coin_per_unit
    moved = 0.0
    for lot in outcome.bonded_lots:
        if lot["people"] > 0.0:
            moved += agents_api.buy_bonded(sim.view("cast")(), buyer, lot["origin"], lot["trade"], lot["people"],
                                           lot["ask"] * coin / lot["people"], lot["carriage"] * coin / lot["people"])
    return moved
