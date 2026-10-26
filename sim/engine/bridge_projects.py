"""Bridge entries the projects module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
code did, and is never cached. Each command applies what the old code did inline. The `legacy_*` views are raw
state the module still mutates in place; they go when that state moves."""
from sim.ledger.api import NoteSpend
from sim.polity.api import RecordBribe
from sim.assembly.api import KEYED, QUOTE
from sim.projects.needed_commands import (ClearMothball, CompleteProject, SettleProjectMaterials)

from . import purchase_rule, projects_precaution
from .agents_port import SimWorld
from .bridge import bridge_command, bridge_view
from .projects_training_advice import training_advice
from .units_prose import money_text


# ---- ventures and production -----------------------------------------------------------------------------------------

@bridge_view("closures", seat_scoped=True)
def closures(sim):
    return sim.state.projects.mothballed


@bridge_view("reopen_fee", kind=QUOTE)
def reopen_fee(sim, node_id):
    return sim.reopen_fee(node_id, sim.reopen_units(node_id))




@bridge_view("running", kind=KEYED)
def running(sim, node_id):
    return sim.running(node_id)


@bridge_view("revenue_estimate", seat_scoped=True)
def revenue_estimate(sim):
    return sim.revenue()


@bridge_view("upkeep", seat_scoped=True)
def upkeep(sim):
    return sim.upkeep()


# ---- projects itself, until progress and completion move ------------------------------------------------------------

@bridge_view("legacy_projects", seat_scoped=True)
def legacy_projects(sim):
    return sim.state.projects


@bridge_view("legacy_order")
def legacy_order(sim):
    return sim.order


@bridge_view("project_cost", kind=QUOTE)
def project_cost(sim, node_id):
    return sim.project_cost(node_id)


@bridge_view("calendar_floor", kind=QUOTE)
def calendar_floor(sim, node_id):
    return sim.calendar_floor(node_id)


@bridge_view("effective_risk", kind=QUOTE)
def effective_risk(sim, node_id):
    return sim.effective_risk(node_id)


@bridge_view("rebuild_work_factor", kind=QUOTE)
def rebuild_work_factor(sim, node_id):
    return sim.rebuild_work_factor(node_id)


@bridge_view("committed_cost", seat_scoped=True)
def committed_cost(sim):
    return sim.committed_spend()


@bridge_view("precaution_spec", kind=QUOTE)
def precaution_spec(sim, node_id):
    return projects_precaution.spec(sim, node_id)


@bridge_view("precaution_extra_cost", kind=QUOTE)
def precaution_extra_cost(sim, node_id, bill):
    return projects_precaution.extra_cost(sim, node_id, bill)


@bridge_view("precaution_extra_hours", kind=QUOTE)
def precaution_extra_hours(sim, node_id):
    return projects_precaution.extra_hours(sim, node_id)


@bridge_view("start_gate_running", kind=QUOTE)
def start_gate_running(sim, node_id, node, ignore_trade, memo, why):
    from .projects_running_gates import check_running_gates
    return check_running_gates(sim, node_id, node, ignore_trade, memo, why)


# ---- materials ------------------------------------------------------------------------------------------------------

@bridge_view("own_output_claim", kind=QUOTE)
def own_output_claim(sim, node_id):
    return sim.project_own_output_claim(node_id)


@bridge_view("bounty_price", kind=QUOTE)
def bounty_price(sim, node_id):
    return sim.bounty_price(node_id)


@bridge_view("material_upfront_refusal", kind=QUOTE)
def material_upfront_refusal(sim, node_id):
    return sim.project_material_upfront_refusal(node_id)


@bridge_view("material_pool", kind=KEYED)
def material_pool(sim, material):
    return sim._material_tag(material)


@bridge_view("generation", seat_scoped=True)
def generation(sim):
    return sim.generation_capacity_kw()


@bridge_view("start_gate_material_seller", kind=QUOTE)
def start_gate_material_seller(sim, node_id, node, ignore_trade, memo, why):
    from .material_availability import check_materials_have_a_seller
    return check_materials_have_a_seller(sim, node_id, node, ignore_trade, memo, why)


# ---- finance --------------------------------------------------------------------------------------------------------

@bridge_view("debt_status", seat_scoped=True)
def debt_status(sim):
    household = sim.state.household
    return {"credit_frozen_until": household.credit_frozen_until, "insolvent_years": household.insolvent_years}


@bridge_view("credit_limit", seat_scoped=True)
def credit_limit(sim):
    return sim.credit_limit()


@bridge_view("funding_capacity", seat_scoped=True)
def funding_capacity(sim):
    return sim.funding_capacity()


@bridge_view("purchase_remedies_text", kind=QUOTE)
def purchase_remedies_text(sim):
    return purchase_rule.remedies_text(sim)


# ---- polity -------------------------------------------------------------------------------------------

@bridge_view("standing", seat_scoped=True)
def standing(sim):
    household = sim.state.household
    return {"protection": household.protection, "scandal": household.scandal, "bribes_year_to_date": household.bribes_ytd}


@bridge_view("state_interest", kind=QUOTE)
def state_interest(sim, node):
    return sim.state_interest(node)


@bridge_view("value_weight", kind=KEYED)
def value_weight(sim, key):
    return sim.value_weights[key]


@bridge_view("start_gate_group_prohibition", kind=QUOTE)
def start_gate_group_prohibition(sim, node_id, node, ignore_trade, memo, why):
    from .interest_groups import check_group_prohibition
    return check_group_prohibition(sim, node_id, node, ignore_trade, memo, why)


# ---- workforce ------------------------------------------------------------------------------------------------------

@bridge_view("hours_available", kind=KEYED, seat_scoped=True)
def hours_available(sim, pool):
    labour = sim.labour
    return {"scholar_hands": labour.scholar_hands_available, "craft_hands": labour.craft_hands_available,
            "director_pool": labour.director_pool, "director_committed": labour.director_hours_committed,
            "hired_cap": labour.hired_cap}[pool]()


@bridge_view("market_supply", kind=KEYED)
def market_supply(sim, trade):
    return sim.labour.market_supply(trade)


@bridge_view("trade_available", kind=KEYED)
def trade_available(sim, trade):
    return sim.labour.trade_available(trade)


@bridge_view("staff_advice", kind=QUOTE)
def staff_advice(sim, kind, deficit):
    return sim.labour.staff_advice(kind, deficit)


@bridge_view("training_advice", kind=QUOTE)
def training_advice_view(sim, trade_id):
    return training_advice(sim.labour, trade_id)


@bridge_view("training_queue", seat_scoped=True)
def training_queue(sim):
    return sim.state.household.training


@bridge_view("project_staffing_shortfall", kind=QUOTE)
def project_staffing_shortfall(sim, node):
    return sim.labour.project_staffing_shortfall(node)


@bridge_view("living_cost", kind=QUOTE)
def living_cost(sim, revenue=None, upkeep=None):
    return sim.living_cost(_rev=revenue, _upkeep=upkeep)


@bridge_view("money_per_labour_hour")
def money_per_labour_hour(sim):
    return sim.labour.money_per_labour_hour()




@bridge_view("mine_operating_cost", seat_scoped=True)
def mine_operating_cost(sim):
    return sim.mine_operating_cost()


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


@bridge_view("research_world")
def research_world(sim):
    return SimWorld(sim)


# ---- commands of owners that have not moved -----------------------------------------------------------------------

@bridge_command(NoteSpend)
def note_spend(sim, command):
    sim.state.household.total_spend += command.amount


@bridge_command(RecordBribe)
def change_standing(sim, command):
    household = sim.state.household
    household.bribes_ytd = command.bribes_year_to_date
    household.scandal = command.scandal
    sim.update_protection()


@bridge_command(SettleProjectMaterials)
def settle_project_materials(sim, command):
    return sim.settle_project_materials(command.node_id)


@bridge_command(ClearMothball)
def clear_mothball(sim, command):
    sim.state.projects.mothballed.discard(command.node_id)


@bridge_command(CompleteProject)
def complete_project(sim, command):
    sim._complete(command.node_id)
