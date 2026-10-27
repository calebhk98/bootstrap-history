"""Bridge entries the knowledge module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached. The `legacy_*` views are state the module shares with the engine; they go when that state moves
(docs/architecture/catalogue/knowledge.md lists each outside writer)."""
from sim.assembly.api import QUOTE

from . import category_traits
from .bridge import bridge_view


@bridge_view("legacy_tree")
def legacy_tree(sim):
    """The tech tree as the engine holds it: node data by id. A re-derivation replaces the object."""
    return sim.nodes


@bridge_view("legacy_fog")
def legacy_fog(sim):
    """Whether the game is played under fog of war (the mode of the game, set at its start)."""
    return sim.state._fog


@bridge_view("legacy_fuzzy_estimates")
def legacy_fuzzy_estimates(sim):
    """Whether estimates are shown blurred (the mode of the game, set at its start or by the options screen)."""
    return sim.state._fuzzy_estimates


@bridge_view("category_trait", kind=QUOTE)
def category_trait(sim, category, trait):
    """Whether the data gives the node category `category` the flag `trait`."""
    return category_traits.has_trait(category, trait)
