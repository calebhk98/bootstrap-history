"""The headline figures a player asks "why did this change?" about.

Each reads the engine function that produces the number; nothing is
recomputed here. Registration is the whole of adding a figure; the ones that only read state
paths are declared in data/ui/figures.json (`figures_data.py`).
"""
from sim.engine.ui_port import cash_book
from .figures import figure
from sim.engine.ui_port import hazards_not_yet_past

HAZARD_KINDS = ("staff_loss", "sack_chance", "output_factor", "real_erosion")


@figure("cash", "cash on hand", unit="money", since=cash_book.causes_since)
def _cash(sim):
    return {"value": sim.capital}


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

from . import figures_world  # noqa: E402,F401  (registers the society figures beside these)
from .figures_data import register_data_figures  # noqa: E402

register_data_figures()
