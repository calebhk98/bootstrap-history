"""Bonded purchase between the agents' strata and the economy's labour market (Complaint 644): which tiles allow it,
who is for sale there, and paying the owners for the people the labour core bought."""
from sim.agents import api as agents_api


def bondage_tiles(sim, economy):
    """The economy's tiles in countries that recognise bondage."""
    return tuple(tile for tile in agents_api.bondage_tiles(sim.actors) if tile in economy.setup.tiles)


def bonded_for_sale(sim, economy):
    """{tile: {trade: people}} the bonded strata offer, on the economy's tiles."""
    return {tile: by_trade for tile, by_trade in agents_api.bonded_for_sale(sim.actors).items()
            if tile in economy.setup.tiles}


def settle_purchases(sim, economy, outcome):
    """Move the people the economy bought out of the bonded strata and pay their owners what the buyers paid
    over the exchange edge (in coin). Returns the people moved."""
    total = sum(outcome.bonded_bought.values())
    if total <= 0.0:
        return 0.0
    price_per_person = outcome.bonded_paid * economy.setup.coin_per_unit / total
    buyer = sim.edge(agents_api.edges.EDGE_ECONOMY)
    moved = 0.0
    for (tile, trade), people in sorted(outcome.bonded_bought.items()):
        moved += agents_api.buy_bonded(sim.actors, buyer, tile, trade, people, price_per_person)
    return moved
