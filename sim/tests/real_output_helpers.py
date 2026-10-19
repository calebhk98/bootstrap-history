"""Shared by the real-output topics: the good, the helpers that complete and run a node and close market years."""
from .harness import *  # noqa: F401,F403

from sim.economy import api as economy_api
from sim.engine import prices as price_solver

# A good one single-output, labour-led entry makes, whose cleared volume answers a cheaper entry by more than the
# world's own year-to-year drift (fat is now a joint product of the herds; a staple's demand barely moves with price).
GOOD = "copper_ore_kg"
YEARS_CLOSED = 1   # the market is one agent-economy year to close, so the fewest years that show each property
YEARS_TO_ENTER = 3   # producers build plant to run a technique over some years before its goods reach the market


def plain_node(game):
    """A node that gates no production entry and earns nothing: completing it changes no recipe."""
    gates = price_solver.all_gate_nodes(price_solver._default_production_entries())
    done = game.state.projects.done
    return next(node_id for node_id in sorted(NODES)
                if node_id not in gates and node_id not in done and not NODES[node_id]["rev"])


def traded_units(game, good=GOOD):
    """Units of the good the agent economy cleared last year."""
    return economy_api.traded_volumes(game.economy.agent.economy()).get(good, 0.0)


def complete(game, node_id):
    game.state.projects.done.add(node_id)
    game._done_changed()


def run(game, node_id):
    """A producer runs the node's techniques: only then do they reach a price."""
    game.state.projects.operating.add(node_id)


def close_years(game, years):
    for _year in range(years):
        game._step_market()
