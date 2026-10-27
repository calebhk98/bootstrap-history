"""Bridge entries the diffusion module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached. Each command applies what the old code did inline. `legacy_country_literacy` is raw
state the module still mutates in place (the strata of the actors' cast); it goes when actors move."""
from sim.agents.api import CountryLiteracy, seed_strata
from sim.assembly.api import KEYED, QUOTE

from . import category_traits
from .bridge import bridge_view


# ---- actors: the strata that hold the reading shares ----

@bridge_view("legacy_country_literacy", kind=KEYED)
def legacy_country_literacy(sim, country):
    """The reading shares of `country` (the home country when None), owned only by the country's strata."""
    sim.view("seeded_actor_registry")()
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


@bridge_view("reputation_gain_of", kind=QUOTE)
def reputation_gain_of(sim, node_id):
    """The standing finishing `node_id` adds."""
    return sim.reputation_gain_of(sim.nodes[node_id])


# ---- mechanics (delete each when the mechanics module publishes it) ----

# ---- public works and the state ----

@bridge_view("coverage")
def coverage(sim):
    """Ids of the works that declare `coverage`."""
    return sim.coverage_nodes()

