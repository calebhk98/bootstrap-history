"""Bridge entries the projects module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached. Each command applies what the old code did inline. """
from sim.ledger.api import CloseSpendYear, NoteSpend
from sim.projects.needed_commands import NoteConcernChange, NoteYearSpend

from . import cause_book
from .bridge import bridge_command

# ---- commands of owners that have not moved -----------------------------------------------------------------------

@bridge_command(NoteSpend)
def note_spend(sim, command):
    sim.state.household.total_spend += command.amount


@bridge_command(NoteYearSpend)
def note_year_spend(sim, command):
    sim._spend_this_year = getattr(sim, "_spend_this_year", 0.0) + command.amount


@bridge_command(CloseSpendYear)
def close_spend_year(sim, command):
    sim.state.household.spend_last_year = getattr(sim, "_spend_this_year", 0.0)
    sim._spend_this_year = 0.0


@bridge_command(NoteConcernChange)
def note_concern_change(sim, command):
    cause_book.record_concern(sim, command.kind, command.node_id, command.cause)
