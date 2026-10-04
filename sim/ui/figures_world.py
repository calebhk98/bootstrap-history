"""Figures about the society around the founder: wages, state notice, epidemics, project throughput.

The engine records no cause for these (Complaints/402), so each gives the value and the live
drivers; whatever the change leaves unexplained shows as the "not itemised" line.
"""
import sim.engine.ui_port as ui_port
from .figures import figure
from sim.engine.ui_port import hazards_not_yet_past


@figure("wages", "wage level against the starting one", unit="index", digits=4)
def _wages(sim):
    return {"value": sim.wage_index,
            "drivers": {"population_scale": sim.pop_scale, "price_index": sim.price_index}}


@figure("state_notice", "how much the state notices you", unit="0 to 1", digits=4)
def _state_notice(sim):
    report = sim.eminence_report()
    return {"value": sim.state_notice(),
            "drivers": {"state_capacity": sim.state_capacity,
                        "household_scale": sim.household_scale(),
                        "eminence": report["now"],
                        "eminence_settles_at": report["settles_at_if_nothing_changes"],
                        "chance_of_ruin_this_year": report["chance_of_ruin_this_year"]}}


@figure("epidemic", "share of staff an epidemic under way takes, after your defences",
        unit="share", digits=4)
def _epidemic(sim):
    loss = 0.0
    for hazard, _start, _end, in_progress in hazards_not_yet_past(sim.civ, sim.year):
        if in_progress and hazard.get("staff_loss"):
            loss = max(loss, sim.hazard_figure("staff_loss", hazard))
    last = ui_port.last_demographic_step(sim)
    drivers = {"disease_burden": ui_port.disease_burden(sim)}
    if last is not None and last.start_total:
        drivers["deaths_per_thousand_last_year"] = 1000 * last.deaths / last.start_total
        drivers["nutrition_ratio"] = last.nutrition_ratio
    return {"value": loss, "drivers": drivers}


@figure("project_throughput", "projects completed by your own work", unit="projects", digits=0)
def _project_throughput(sim):
    # the change since last year is this year's completions
    return {"value": len(sim.done - sim.granted),
            "drivers": {"active_projects": len(sim.active), "throttle": sim.throttle,
                        "employees": sum(sim.employees.values())}}
