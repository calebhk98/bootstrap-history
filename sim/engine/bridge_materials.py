"""Bridge entries the materials module reads, and the market commands it sends, until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached."""
from sim.assembly.api import KEYED, QUOTE

from . import view_share
from .bridge import bridge_view
from .data import hard_pre


# ---- the tree and the seat's projects ----

@bridge_view("hard_prerequisites", kind=KEYED)
def hard_prerequisites(sim, node_id):
    """Every prerequisite of a node that is mandatory: its `pre`, and the requirement groups that offer one real node."""
    return hard_pre(sim.nodes, node_id)


@bridge_view("project_versions", seat_scoped=True)
def project_versions(sim):
    """(the acting seat's active-projects version, its done-set version): move when a project starts, finishes or is lost."""
    return (sim.household.active_version, sim.household.done_version)


@bridge_view("empire_output")
def empire_output(sim):
    """The reference empire's yearly output of the tracked commodities, by commodity: {"t_per_yr": ...}."""
    return sim.res["empire_output_100ad"]


# ---- the catalogue of commodities, the price epoch and the producers ----

# ---- projects' costs and what the seat can pay ----

@bridge_view("shared_bill", kind=QUOTE)
def shared_bill(sim, node_id, compute):
    """A project's material bill, reused inside a view's scope while the world and the node's stock hold."""
    return view_share.of(sim)._shared_bill(node_id, compute)


@bridge_view("failure_reset_share")
def failure_reset_share(sim):
    """The share of a failed project's bill that is lost."""
    return sim.FAILURE_RESET_SHARE
