"""Bridge entries the projects module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached. Each command applies what the old code did inline. The `legacy_*` views are raw
state the module still mutates in place; they go when that state moves."""
from sim.assembly.api import KEYED, QUOTE
from sim.ledger.api import NoteSpend
from sim.projects.needed_commands import ClearMothball, NoteConcernChange, NoteYearSpend, OpenVenture

from . import cause_book
from .bridge import bridge_command, bridge_view
from .units_prose import money_text


# ---- ventures and production -----------------------------------------------------------------------------------------

@bridge_view("closures", seat_scoped=True)
def closures(sim):
    return sim.state.projects.mothballed


@bridge_view("reopen_fee", kind=QUOTE)
def reopen_fee(sim, node_id):
    return sim.reopen_fee(node_id, sim.reopen_units(node_id))


@bridge_view("opening_fee", kind=QUOTE)
def opening_fee(sim, node_id, units=None):
    """(charge, size) for opening a concern now; `open` charges exactly this."""
    return sim.opening_fee(node_id, units)


@bridge_view("venture_hands", kind=KEYED)
def venture_hands(sim, node_id):
    """(scholars, craftsmen) of your own that running the concern ties up."""
    return sim.venture_hands(node_id)


@bridge_view("venture_foreman_free", kind=QUOTE)
def venture_foreman_free(sim, trade, excluding=None):
    """Employed specialists of `trade` still free to supervise another concern."""
    return sim.venture_foreman_free(trade, excluding)


@bridge_view("venture_staff_used")
def venture_staff_used(sim):
    """(scholars, craftsmen) tied up supervising what is already open."""
    return sim.venture_staff_used()


@bridge_view("venture_capex", kind=KEYED)
def venture_capex(sim, node_id):
    return sim.venture_capex(node_id)


@bridge_view("venture_real_earnings", kind=QUOTE)
def venture_real_earnings(sim, node_id, units=None, fully_ramped=False, with_output_factor=True):
    return sim.venture_real_earnings(node_id, units, fully_ramped, with_output_factor)


@bridge_view("venture_real_upkeep", kind=QUOTE)
def venture_real_upkeep(sim, node_id, units=None):
    return sim.venture_real_upkeep(node_id, units)


# ---- projects itself: the record of what is in hand, until it moves ------------------------------------------------

@bridge_view("legacy_projects", seat_scoped=True)
def legacy_projects(sim):
    return sim.state.projects


@bridge_view("legacy_order")
def legacy_order(sim):
    return sim.order


@bridge_view("project_cost", kind=QUOTE)
def project_cost(sim, node_id):
    return sim.project_cost(node_id)


# ---- living stock -----------------------------------------------------------------------------------------------------

@bridge_view("start_gate_unheld_stock", kind=QUOTE)
def start_gate_unheld_stock(sim, node_id, node, ignore_trade, memo, why):
    from .forward_living_stock import check_unheld_stock
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


@bridge_command(ClearMothball)
def clear_mothball(sim, command):
    sim.state.projects.mothballed.discard(command.node_id)


@bridge_command(NoteConcernChange)
def note_concern_change(sim, command):
    cause_book.record_concern(sim, command.kind, command.node_id, command.cause)


@bridge_command(OpenVenture)
def open_venture(sim, command):
    return sim.open_venture(command.node_id, units=command.units)
