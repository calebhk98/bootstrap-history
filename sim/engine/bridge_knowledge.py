"""Bridge entries the knowledge module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached. The `legacy_*` views are state the module shares with the engine; they go when that state moves
(docs/architecture/catalogue/knowledge.md lists each outside writer)."""
from sim.assembly.api import KEYED, QUOTE
from sim.knowledge.needed_commands import RefreshDoneCaches

from . import category_traits
from .bridge import bridge_command, bridge_view


@bridge_view("legacy_tree")
def legacy_tree(sim):
    """The tech tree as the engine holds it: node data by id. A re-derivation replaces the object."""
    return sim.nodes


@bridge_view("legacy_fog")
def legacy_fog(sim):
    """Whether the game is played under fog of war (the mode of the game, set at its start)."""
    return sim.state._fog


@bridge_view("legacy_seats")
def legacy_seats(sim):
    """Every seat's saved state, by seat id."""
    return sim.state.seats


@bridge_view("category_trait", kind=QUOTE)
def category_trait(sim, category, trait):
    """Whether the data gives the node category `category` the flag `trait`."""
    return category_traits.has_trait(category, trait)


@bridge_view("relied_on_running", kind=KEYED)
def relied_on_running(sim, node_id):
    """Whether some node requires `node_id` running."""
    return sim.relied_on_running(node_id)


@bridge_view("on_road_to_goal", kind=QUOTE)
def on_road_to_goal(sim, node_id):
    """Whether the goal needs `node_id` (a yes or no, with no distance, so it names no route the player has not been shown)."""
    return sim.on_road_to_goal(node_id)


@bridge_command(RefreshDoneCaches)
def refresh_done_caches(sim, command):
    sim._done_changed()
