"""Route dues reaching their holders. The economy's merchants pay each toll and port due, as money, to an account of the
tile's holder (economy/route_dues.py); after the year's clearing that money goes over the exchange edge and is paid to
the holder in coin: a seat as its household, anyone else to the government of that country (opened when the cast
holds none yet)."""
from sim.agents.api import edges
from sim.economy import api as economy_api
from sim.economy.api import EDGE_EXCHANGE
from sim.ledger.api import ReceiveFromEdge, ReceiveFromExchange


def settle(sim, economy) -> None:
    coin = economy_api.coin_per_unit(economy)
    for holder in economy_api.tile_holders(economy):
        units = economy_api.settle_agent_takings(economy, economy_api.route_dues_account(holder), EDGE_EXCHANGE)
        if units <= 0.0:
            continue
        if holder in sim.state.seats:
            with sim.scenario.act_as(holder):
                sim.send(ReceiveFromEdge(edges.EDGE_CUSTOMERS, units * coin, "route dues"))
        else:
            government = sim.scenario.actors.countries.ensure_government(holder)
            sim.send(ReceiveFromExchange(government.actor_id, units * coin, "route dues"))
