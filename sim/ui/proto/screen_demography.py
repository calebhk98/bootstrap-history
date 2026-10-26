"""The `demography` screen (Complaints/94): age cohorts, last year's births
and deaths, disease and food pressure, and the trades, read from the
population model and from population_report.
"""
import sim.engine.ui_port as ui_port
from .demography_history import recent_shocks, recovery


def _last_year(sim):
    flows = ui_port.last_demographic_step(sim)
    if flows is None:
        return _last_year_from_record(sim)
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


def _last_year_from_record(sim):
    record = sim.view("yearly_record")()
    if not record:
        return None
    last = record[-1]
    return {"births": last["births"], "deaths": last["deaths"],
            "nutrition_ratio": last["nutrition_ratio"], "year": last["year"]}


def _epidemics_under_way(sim):
    """The pathogens someone is infected with now, each with the model's forecast of the year's deaths."""
    return [{"name": row["name"], "infected": row["infected"], "expected_deaths": row["expected_deaths"]}
            for row in ui_port.epidemic_forecast(sim)["by_pathogen"]]


def demography_report(sim):
    population = sim.population
    total = population.total
    change = sim.view("population_change_last_year")()
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
        "disease_burden": round(ui_port.disease_burden(sim), 4),
        "epidemics_under_way": _epidemics_under_way(sim),
        "epidemic_forecast": {key: value for key, value in ui_port.epidemic_forecast(sim).items()
                              if key != "expected_deaths_by_tile"},
        "recent_shocks": recent_shocks(sim.view("yearly_record")()),
        "recovery": recovery(sim.view("yearly_record")(), total, sim.year),
        "wage_index": round(sim.wage_index, 4),
        "trades": sim.labour.population_report()["trades"],
        "not_held": ["the model has three age cohorts, not single years of age",
                     "the recovery figure extrapolates recent growth; it does not model "
                     "food, disease or war ahead",
                     "the yearly record keeps only the most recent years of totals, "
                     "births and deaths, not the age cohorts"],
    }
