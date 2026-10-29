"""Bridge entries the hazards module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached. Each command applies what the old hazard code did inline, in the same order. The `legacy_*`
views are raw state the module still needs; they go when that state moves."""
from sim.projects.api import ShutForgotten
from sim.workforce.api import NoteWageShock

from . import cause_book
from .bridge import bridge_command, bridge_view


# ---- commands of owners that have not moved -------------------------------------------------------------------------

@bridge_command(NoteWageShock)
def note_wage_shock(sim, command):
    cause_book.record_wage_shock(sim, command.cause, command.index_before)


@bridge_command(ShutForgotten)
def shut_forgotten(sim, command):
    projects = sim.state.projects
    for node_id in command.node_ids:
        projects.operating.discard(node_id)
        projects.mothballed.discard(node_id)
