"""Bridge entries the projects module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached. Each command applies what the old code did inline. The `legacy_*` views are raw
state the module still mutates in place; they go when that state moves."""
from sim.assembly.api import KEYED, QUOTE
from sim.ledger.api import CloseSpendYear, NoteSpend
from sim.projects.needed_commands import NoteConcernChange, NoteYearSpend

from . import cause_book
from .bridge import bridge_command, bridge_view
from .units_prose import money_text


# ---- projects itself: the record of what is in hand, until it moves ------------------------------------------------

@bridge_view("legacy_projects", seat_scoped=True)
def legacy_projects(sim):
    return sim.state.projects


@bridge_view("legacy_order")
def legacy_order(sim):
    return sim.order


# ---- living stock -----------------------------------------------------------------------------------------------------

@bridge_view("start_gate_unheld_stock", kind=QUOTE)
def start_gate_unheld_stock(sim, node_id, node, ignore_trade, memo, why):
    from .blocker_unheld_stock import check_unheld_stock
    return check_unheld_stock(sim, node_id, node, ignore_trade, memo, why)


# ---- reporting, seats and the root ---------------------------------------------------------------------------------

@bridge_view("money_text", kind=QUOTE)
def money_text_view(sim, amount, grouped=False, short=False):
    return money_text(amount, sim, grouped=grouped, short=short)


@bridge_view("automation")
def automation(sim):
    return {"manual": sim.manual, "bounty_set": sim.bounty_set}


@bridge_view("society_name")
def society_name(sim):
    return sim.civ.get("name", "this society")


@bridge_view("horizon_end_year")
def horizon_end_year(sim):
    return getattr(sim, "end_year", None) or (sim.cfg["start_year"] + sim.cfg["horizon_years"])


@bridge_view("project_limits")
def project_limits(sim):
    return {"base": sim.MAX_ACTIVE_PROJECTS_BASE, "per_director_hours": sim.MAX_ACTIVE_PROJECTS_PER_DIRECTOR_HOURS,
            "per_scholar": sim.MAX_ACTIVE_PROJECTS_PER_SCHOLAR, "per_artisan": sim.MAX_ACTIVE_PROJECTS_PER_ARTISAN}


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
