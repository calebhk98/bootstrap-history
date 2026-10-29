"""Bridge entries the hazards module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached. Each command applies what the old hazard code did inline, in the same order. The `legacy_*`
views are raw state or the engine's own switches the module still needs; they go when that state moves."""
from sim.assembly.api import QUOTE
from sim.projects.api import ShutForgotten
from sim.workforce.api import NoteWageShock

from . import cause_book, event_causes
from .bridge import bridge_command, bridge_view


# ---- core: the engine's own switches and raw state ----------------------------------------------------------------

@bridge_view("legacy_act_as", kind=QUOTE)
def legacy_act_as(sim, seat_id):
    """The context in which `seat_id` is the acting seat (the engine's `act_as`); the module has no way to switch seats."""
    return sim.act_as(seat_id)


@bridge_view("effective_hazard", kind=QUOTE)
def effective_hazard(sim, hazard):
    """(the dated event as its stated causes leave it now, or None; the report of which causes hold)."""
    return event_causes.effective_hazard(sim, hazard)


# ---- projects and ventures ------------------------------------------------------------------------------------------


# ---- polity, workforce, resources, actors ---------------------------------------------------------------------------


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
