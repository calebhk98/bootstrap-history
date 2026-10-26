"""Bridge entries the hazards module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached. Each command applies what the old hazard code did inline, in the same order. The `legacy_*`
views are raw state or the engine's own switches the module still needs; they go when that state moves."""
from sim.assembly.api import KEYED, QUOTE
from sim.projects.api import ResetProjectProgress, ShutForgotten
from sim.reporting.api import RecordEvent
from sim.workforce.api import NoteWageShock, ReportStaffReduction, ScaleDeputies, SurviveStaff, rules as workforce_rules

from . import cause_book, event_causes, mod_effects
from .bridge import bridge_command, bridge_view
from .data import closure, critical_path


# ---- core: the engine's own switches and raw state ----------------------------------------------------------------

@bridge_view("events_enabled")
def events_enabled(sim):
    """Whether the game runs with its random events and hazards (a test or a replay may turn them off)."""
    return sim.events


@bridge_view("legacy_act_as", kind=QUOTE)
def legacy_act_as(sim, seat_id):
    """The context in which `seat_id` is the acting seat (the engine's `act_as`); the module has no way to switch seats."""
    return sim.act_as(seat_id)


@bridge_view("legacy_said_once")
def legacy_said_once(sim):
    """The set of notices the hazards and the levy have already told once (mutated in place: a debt)."""
    return sim.state.scenario._said_condition


@bridge_view("effective_hazard", kind=QUOTE)
def effective_hazard(sim, hazard):
    """(the dated event as its stated causes leave it now, or None; the report of which causes hold)."""
    return event_causes.effective_hazard(sim, hazard)


# ---- knowledge and the tree -----------------------------------------------------------------------------------------

@bridge_view("losable_node_ids", kind=QUOTE, seat_scoped=True)
def losable_node_ids(sim, keep_dispersed=True):
    """Built nodes a loss event may take: not inherited, not a measured goal, and by default not a dispersed corpus."""
    return sim.losable_node_ids(keep_dispersed)


@bridge_view("critical_path", kind=QUOTE)
def critical_path_view(sim, goal_id):
    """(the longest chain's calendar years, the node ids on it) from the roots to `goal_id`."""
    return critical_path(sim.nodes, goal_id)


@bridge_view("tree_closure", kind=QUOTE)
def tree_closure(sim, goal_id):
    """Every node the goal needs, following the mandatory prerequisites."""
    return closure(sim.nodes, goal_id)


# ---- projects and ventures ------------------------------------------------------------------------------------------

@bridge_view("active_projects", seat_scoped=True)
def active_projects(sim):
    """{node id: the project's record} of the acting seat's projects in hand (the object itself)."""
    return sim.state.projects.active


@bridge_view("closure_record", kind=KEYED, seat_scoped=True)
def closure_record(sim, node_id):
    """{reason, year} of a shut work that records why, or None."""
    return sim.state.projects.closures.get(node_id)


@bridge_view("closed_by_choice")
def closed_by_choice(sim):
    """The closure reason of a work the founder shut by choice."""
    return sim.CLOSED_BY_CHOICE


# ---- polity, workforce, resources, actors ---------------------------------------------------------------------------

@bridge_view("staff_snapshot", seat_scoped=True)
def staff_snapshot(sim):
    """Headcount by trade now, to diff against after something trims it."""
    return sim.labour.staff_snapshot()


@bridge_view("wage_index")
def wage_index(sim):
    return sim.wage_index


@bridge_view("country_strata", kind=KEYED)
def country_strata(sim, country):
    """[{members, shortfall}] of the country's strata: how many they are and the share of each need they leave unmet."""
    return [{"members": actor.record.members, "shortfall": actor.record.shortfall} for actor in mod_effects.strata_of(sim, country)]


# ---- commands of owners that have not moved -------------------------------------------------------------------------

@bridge_command(SurviveStaff)
def survive_staff(sim, command):
    household = sim.state.household
    survive = workforce_rules.surviving_people
    household.scholars = survive(sim.rng, household.scholars, command.survival_share)
    household.artisans = survive(sim.rng, household.artisans, command.survival_share)
    for trade in sorted(household.employees):
        survivors = survive(sim.rng, household.employees[trade], command.survival_share)
        if survivors > 0:
            household.employees[trade] = survivors
        else:
            household.employees.pop(trade)


@bridge_command(ScaleDeputies)
def scale_deputies(sim, command):
    sim.state.household.directors_extra *= command.share


@bridge_command(ReportStaffReduction)
def report_staff_reduction(sim, command):
    sim.labour.log_staff_reduction(command.cause, command.before)


@bridge_command(NoteWageShock)
def note_wage_shock(sim, command):
    cause_book.record_wage_shock(sim, command.cause, command.index_before)


@bridge_command(ShutForgotten)
def shut_forgotten(sim, command):
    projects = sim.state.projects
    for node_id in command.node_ids:
        projects.operating.discard(node_id)
        projects.mothballed.discard(node_id)


@bridge_command(ResetProjectProgress)
def reset_project_progress(sim, command):
    projects = sim.state.projects
    for node_id in sorted(projects.active):
        projects.active[node_id]["ph_left"] = sim.nodes[node_id]["ph"]
        projects.active[node_id]["yrs"] = 0.0


