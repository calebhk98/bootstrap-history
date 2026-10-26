"""Bridge entries the diffusion module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached. Each command applies what the old code did inline. `legacy_country_literacy` is raw
state the module still mutates in place (the strata of the actors' cast); it goes when actors move."""
from sim.agents.api import CountryLiteracy, seed_strata
from sim.assembly.api import KEYED, QUOTE
from sim.workforce.api import NoteTradeSpread, SetEmployed

from . import category_traits, seat_builds
from .agents_port_cast import seed_opening_cast
from .bridge import bridge_command, bridge_view
from .data import TRADES_ABSENT


# ---- actors: the strata that hold the reading shares ----

@bridge_view("legacy_country_literacy", kind=KEYED)
def legacy_country_literacy(sim, country):
    """The reading shares of `country` (the home country when None), owned only by the country's strata."""
    seed_opening_cast(sim)
    if not sim.actors.of_kind("stratum"):
        seed_strata(sim.actors, None)
    home = sim.actors.state.home_country
    country = country or home
    return CountryLiteracy(actor for actor in sim.actors.of_kind("stratum")
                           if (actor.record.country or home) == country)


@bridge_view("state_knowledge")
def state_knowledge(sim):
    """The nodes the home government holds."""
    return sim.state_treasury().knowledge


@bridge_view("seat_party", kind=KEYED)
def seat_party(sim, seat_id):
    return sim.seat_party(seat_id)


# ---- seats ----

@bridge_view("seat_list")
def seat_list(sim):
    """{joined: every seat's id, playing: the seats still playing}."""
    return {"joined": list(sim.state.seats), "playing": sim.playing_seats()}


@bridge_view("seat_holders", kind=QUOTE)
def seat_holders(sim, node_id):
    """Ids of the seats that hold `node_id` at all, built or granted."""
    return seat_builds.holders_of(sim.state.seats, node_id)


@bridge_view("built_by_any_seat", kind=QUOTE)
def built_by_any_seat(sim, among):
    """Every node of `among` some seat built itself."""
    return seat_builds.built_by_any(sim.state.seats, among)




# ---- knowledge and production ----

@bridge_view("tech_effects", kind=KEYED)
def tech_effects(sim, node_id):
    """What finishing `node_id` does to the society (the effects table), or None."""
    return sim._tech_effects.get(node_id)


@bridge_view("diffusion_traits")
def diffusion_traits(sim):
    """The categories knowledge spreads by, in priority order: trait name to its entry."""
    return category_traits.diffusion_traits()






@bridge_view("venture_opened_year", kind=QUOTE)
def venture_opened_year(sim, node_id, default):
    return sim.state.projects.business.opened_year_of(node_id, default)


@bridge_view("techniques_in_use", seat_scoped=True)
def techniques_in_use(sim):
    """Nodes whose production entries some producer runs now."""
    return sim.techniques_in_use()


@bridge_view("reputation_gain_of", kind=QUOTE)
def reputation_gain_of(sim, node_id):
    """The standing finishing `node_id` adds."""
    return sim.reputation_gain_of(sim.nodes[node_id])


# ---- mechanics (delete each when the mechanics module publishes it) ----

# ---- workforce ----

@bridge_view("literacy_references")
def literacy_references(sim):
    """The literacy figures hiring and research are measured against."""
    labour = sim.labour
    return {"factor_cap": labour.LITERACY_FACTOR_CAP, "reference_elite": labour.LITERACY_REFERENCE_ELITE,
            "reference_general": labour.LITERACY_REFERENCE_GENERAL}


@bridge_view("literacy_capacity", kind=KEYED, seat_scoped=True)
def literacy_capacity(sim, trade):
    """The most people of `trade` the country's literacy lets the seat hire or teach."""
    return sim.labour.literate_capacity(trade)


@bridge_view("farm_share_of_hours", seat_scoped=True)
def farm_share_of_hours(sim):
    return sim.labour.farm_share_of_hours()


@bridge_view("trade_spread", seat_scoped=True)
def trade_spread(sim):
    """{absent: the trades that do not exist until taught, created: those the seat taught, endemic: those the society
    has, introduced_year: the year each was first seen taught}; the last three are live."""
    household = sim.state.household
    return {"absent": sorted(TRADES_ABSENT), "created": household.trades_created, "endemic": household.trades_endemic,
            "introduced_year": household.trade_introduced_year}


# ---- disease and the state ----

@bridge_view("coverage")
def coverage(sim):
    """Ids of the works that declare `coverage`."""
    return sim.coverage_nodes()


@bridge_view("disease_burden")
def disease_burden(sim):
    return sim._disease_burden()


@bridge_view("disease_burden_held", kind=KEYED)
def disease_burden_held(sim, node_id):
    return sim.disease_burden_held(node_id)


@bridge_view("disease_burden_weights")
def disease_burden_weights(sim):
    """{node id: its population weight} for the technologies that make up the disease burden, in tree order."""
    return {tech_id: sim._tech_effects[tech_id].get("population", 0.0) for tech_id in sim.DISEASE_BURDEN_TECH_IDS}


# ---- commands ----

@bridge_command(SetEmployed)
def set_employed(sim, command):
    sim.labour.set_employed(command.trade, command.headcount)
    sim.labour.resync_pools()


@bridge_command(NoteTradeSpread)
def note_trade_spread(sim, command):
    household = sim.state.household
    if command.introduced_year is not None:
        household.trade_introduced_year[command.trade] = command.introduced_year
    if command.endemic:
        household.trades_endemic.add(command.trade)
