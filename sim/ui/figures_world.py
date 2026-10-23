"""Figures about the society around the founder: wages, state notice, epidemics, project throughput.

Wages and state notice read their causes from the cause book; the others give the value and the
live drivers, and whatever the change leaves unexplained shows as its own line.
"""
import sim.engine.ui_port as ui_port
from .figures import figure
from sim.engine.ui_port import cause_book


def _wage_causes(sim, year):
    return cause_book.causes_since(sim, cause_book.WAGE, year)


def _notice_causes(sim, year):
    return cause_book.causes_since(sim, cause_book.NOTICE, year)


@figure("wages", "wage level against the starting one", unit="index", digits=4, since=_wage_causes)
def _wages(sim):
    return {"value": sim.wage_index,
            "drivers": {"population_scale": sim.pop_scale, "price_index": sim.price_index}}


@figure("state_notice", "how much the state notices you", unit="0 to 1", digits=4,
        since=_notice_causes)
def _state_notice(sim):
    report = sim.eminence_report()
    return {"value": sim.state_notice(),
            "drivers": {"state_reach": sim.state_reach(),
                        "household_scale": sim.household_scale(),
                        "eminence": report["now"],
                        "eminence_settles_at": report["settles_at_if_nothing_changes"],
                        "chance_of_ruin_this_year": report["chance_of_ruin_this_year"]}}


@figure("epidemic", "share of working-age people the epidemics under way are forecast to take this year, after your defences",
        unit="share", digits=4)
def _epidemic(sim):
    forecast = ui_port.epidemic_forecast(sim)
    loss = forecast["expected_working_age_share"]
    last = ui_port.last_demographic_step(sim)
    drivers = {"disease_burden": ui_port.disease_burden(sim), "expected_deaths": forecast["expected_deaths"],
               "people_infected": sum(row["infected"] for row in forecast["by_pathogen"])}
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
