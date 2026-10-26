"""Bridge entries the freight module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached. `legacy_world_map` is the map handle the geography package's searches take; it goes when
the land module publishes its tile facts."""
from sim.agents.api import EDGE_SAVERS, GOVERNMENT_PREFIX, ledger
from sim.assembly.api import KEYED, QUOTE
from sim.ledger.api import PayActor

from . import action_results
from .bridge import bridge_command, bridge_view


# ---- knowledge, workforce, finance and prices ----

@bridge_view("techniques_with_results", kind=QUOTE)
def techniques_with_results(sim, techniques):
    """`techniques` with the routes, partners and knowledge their nodes return."""
    return action_results.expand(sim.nodes, techniques)


@bridge_view("wage", kind=KEYED)
def wage(sim, trade):
    """Money one hour of a trade is worth on the wage schedule (the labour market's quote is `hour_wage`)."""
    return sim.labour.wage_per_hour(trade)


@bridge_view("trade_population", kind=KEYED)
def trade_population(sim, trade):
    """An estimate of the people who ply a trade across the country."""
    return sim.labour.national_trade_population(trade)


@bridge_view("market_rate")
def market_rate(sim):
    return sim.market_rate()


@bridge_view("households_loanable_funds")
def households_loanable_funds(sim):
    """Funds households put into the loanable pool at the last meeting of the capital market; none before it has met."""
    return sim.actors.state.purses.offers.get(EDGE_SAVERS, 0.0)


@bridge_view("material_prices")
def material_prices(sim):
    """The price table: the same object while the prices are unchanged."""
    return sim._material_prices()


@bridge_view("material_price", kind=KEYED)
def material_price(sim, tag):
    """Money per kg of a material key or curated commodity; None if it cannot be priced."""
    return sim._material_price_per_kg(tag)


# ---- land and markets ----

@bridge_view("legacy_world_map")
def legacy_world_map(sim):
    return sim.world_map


@bridge_view("held_techniques", kind=QUOTE)
def held_techniques(sim, include_starting):
    """The techniques and results held and running, with the civilisation's starting ones or without."""
    return sim.held_and_running(include_starting)


@bridge_view("built_ways")
def built_ways(sim):
    """The ways built, by way key."""
    return sim.state.economy.improvements


@bridge_view("material_source_tiles", kind=KEYED)
def material_source_tiles(sim, material):
    return sim.geography.source_tiles(material)


@bridge_view("route_km_to", kind=QUOTE)
def route_km_to(sim, tiles):
    return sim.geography.route_km_to(tiles)


@bridge_view("goods_carried_last_year")
def goods_carried_last_year(sim):
    """Last year's goods carried between the economy's tiles, {origin: {destination: tonnes}}."""
    return sim.economy.agent.carried_last_year()


@bridge_view("working_age")
def working_age(sim):
    return sim.population.working_age


# ---- polity and the ledger ----

@bridge_view("holder_treasury", kind=KEYED)
def holder_treasury(sim, holder):
    """The id of the account a country's or seat's dues are paid into: the seat itself (paid as its party), else the
    country's government."""
    if holder in sim.state.seats:
        return holder
    government = sim.actors.government_of(holder)
    return government.actor_id if government is not None else GOVERNMENT_PREFIX + str(holder)


@bridge_command(PayActor)
def pay_actor(sim, command):
    """The payer pays the payee through the ledger's transfer; a government not yet in the cast is opened."""
    if command.payee in sim.state.seats:
        payee = sim.seat_party(command.payee)
    else:
        payee = sim.actors.get(command.payee) or sim.actors.ensure_government(command.payee[len(GOVERNMENT_PREFIX):])
    ledger.transfer(sim.actors.get(command.payer), payee, command.amount, command.purpose)
