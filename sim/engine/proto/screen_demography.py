"""The `demography` screen (Complaints/94): age cohorts, last year's births
and deaths, disease and food pressure, and the trades, read from the
population model and from population_report.
"""
from ..hazard_window import hazards_not_yet_past


def _last_year(sim):
    flows = sim._last_demographic_step
    if flows is None:
        return None
    start = flows.start_total
    return {
        "births": round(flows.births), "deaths": round(flows.deaths),
        "immigration": round(flows.immigration), "emigration": round(flows.emigration),
        "deaths_children": round(flows.deaths_children),
        "deaths_working_age": round(flows.deaths_working_age),
        "deaths_elderly": round(flows.deaths_elderly),
        "births_per_thousand": round(1000 * flows.births / start, 1) if start else None,
        "deaths_per_thousand": round(1000 * flows.deaths / start, 1) if start else None,
        "nutrition_ratio": round(flows.nutrition_ratio, 4),
    }


def _hazards_costing_people(sim):
    return [{"name": hazard.get("name", "hazard"), "years": [year_start, year_end],
             "share_of_staff_lost": hazard["staff_loss"]}
            for hazard, year_start, year_end, in_progress
            in hazards_not_yet_past(sim.civ, sim.year)
            if in_progress and hazard.get("staff_loss")]


def demography_report(sim):
    population = sim.population
    total = population.total
    change = sim.state.population.population_change_last_year
    return {
        "ok": True,
        "population": round(total),
        "cohorts": {"children": round(population.children),
                    "working_age": round(population.working_age),
                    "elderly": round(population.elderly)},
        "working_age_share": round(population.working_age / total, 4) if total else None,
        "reference_population_at_start": round(float(sim.civ.get("population", 0.0))),
        "change_in_the_last_step": change,
        "last_year": _last_year(sim),
        "disease_burden": round(sim._disease_burden(), 4),
        "epidemics_under_way": _hazards_costing_people(sim),
        "wage_index": round(sim.wage_index, 4),
        "trades": sim.population_report()["trades"],
        "not_held": ["the model has three age cohorts, not single years of age",
                     "no recovery timeline: nothing here projects the population forward",
                     "last year's births and deaths exist only for a year simulated "
                     "in this session; a freshly loaded save shows none until the next step"],
    }
