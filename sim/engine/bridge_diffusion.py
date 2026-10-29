"""Bridge entries the diffusion module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached. Each command applies what the old code did inline. `legacy_country_literacy` is raw
state the module still mutates in place (the strata of the actors' cast); it goes when actors move."""
from sim.assembly.api import KEYED

from . import category_traits
from .bridge import bridge_view


# ---- actors: the strata that hold the reading shares ----

# ---- knowledge and production ----

@bridge_view("tech_effects", kind=KEYED)
def tech_effects(sim, node_id):
    """What finishing `node_id` does to the society (the effects table), or None."""
    return sim._tech_effects.get(node_id)


@bridge_view("diffusion_traits")
def diffusion_traits(sim):
    """The categories knowledge spreads by, in priority order: trait name to its entry."""
    return category_traits.diffusion_traits()


# ---- mechanics (delete each when the mechanics module publishes it) ----

