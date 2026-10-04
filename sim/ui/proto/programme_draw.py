"""The yearly money a programme's earlier starts still draw, so its caps cover standing work."""

from .dispatch_ventures import _rush_cost_left
from .portfolio_scale import annual_absorption

STARTED_KEY = "started_ids"


def standing_draw(sim, programme):
    """Annual draw of projects this programme started that are still running; forgets finished ones."""
    running = [node_id for node_id in programme.get(STARTED_KEY, []) if node_id in sim.active]
    programme[STARTED_KEY] = running
    return sum(annual_absorption(_rush_cost_left(sim, node_id), sim.nodes[node_id]) for node_id in running)


def remember_starts(programme, started):
    programme[STARTED_KEY] = list(programme.get(STARTED_KEY, [])) + [item["id"] for item in started]
