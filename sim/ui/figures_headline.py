"""The headline figures a player asks "why did this change?" about.

Each reads the engine function that produces the number; nothing is
recomputed here. Registration is the whole of adding a figure.
"""
from sim.engine.ui_port import cash_book
from .figures import figure
from sim.engine.ui_port import hazards_not_yet_past

HAZARD_KINDS = ("staff_loss", "sack_chance", "output_factor", "real_erosion")


@figure("cash", "cash on hand", unit="money", since=cash_book.causes_since)
def _cash(sim):
    return {"value": sim.capital}


@figure("income", "recurring revenue per year", unit="money per year")
def _income(sim):
    return {"value": sim.revenue(), "components": sim.revenue_sources()}


@figure("upkeep", "running costs per year", unit="money per year")
def _upkeep(sim):
    return {"value": sim.upkeep(), "components": sim.upkeep_by_concern()}


@figure("recurring_net", "recurring net per year", unit="money per year")
def _recurring_net(sim):
    interest = max(0.0, -sim.capital) * sim.debt_interest_rate()
    return {
        "value": sim.recurring_net(),
        "components": {
            "revenue": sim.revenue_capacity(),
            "running costs of concerns": -sim.upkeep(),
            "living costs": -sim.living_cost(),
            "mine running costs": -sim.mine_operating_cost(),
            "interest on arrears": -interest,
        },
        "drivers": {"price_index": sim.price_index, "wage_index": sim.wage_index},
    }


@figure("population", "population", unit="people", digits=0)
def _population(sim):
    population = sim.population
    return {"value": population.total,
            "components": {"children": population.children,
                           "working age": population.working_age,
                           "elderly": population.elderly}}


def _literacy(sim, field, ceiling):
    return {"value": float(sim.civ.get(field, 0.0)),
            "drivers": {"effective_schooling_flow": sim.effective_schooling_flow(),
                        "ceiling": ceiling}}


@figure("literacy_general", "general literacy", unit="share of the population", digits=4)
def _literacy_general(sim):
    return _literacy(sim, "literacy_general", sim.literacy_ceiling_general())


@figure("literacy_elite", "elite literacy", unit="share of the lettered class", digits=4)
def _literacy_elite(sim):
    return _literacy(sim, "literacy_elite", sim.literacy_ceiling_elite())


@figure("price_index", "price level against the starting one", unit="index", digits=4)
def _price_index(sim):
    return {"value": sim.price_index, "drivers": {"wage_index": sim.wage_index}}


@figure("hazard", "the nearest hazard's worst harm after your defences", unit="harm", digits=4)
def _hazard(sim):
    for hazard, _start, _end, _in_progress in hazards_not_yet_past(sim.civ, sim.year):
        kinds = [kind for kind in HAZARD_KINDS if kind in hazard]
        if not kinds:
            continue
        kind = max(kinds, key=lambda candidate: sim.hazard_figure(candidate, hazard))
        drivers = {"unmitigated " + kind: hazard[kind]}
        for entry in sim.hazard_relief_entries(kind):
            drivers[entry["label"] + " (multiplies the harm by)"] = entry["factor"]
        return {"value": sim.hazard_figure(kind, hazard), "drivers": drivers}
    return {"value": None}
