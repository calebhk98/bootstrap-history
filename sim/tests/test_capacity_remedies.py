"""capacity_remedies: the capacity screen offers the commands that would end each shortage (Complaints 90, 189).

The rules are tested on plain inputs: the remedy rows (a stub game stands in for the household and the remedy plan),
the sizing of a mine or a nitre bed, and the rendering."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

import types

from sim.resources.sizing import mine_shortfall_after_sinking, mine_size_tonnes, nitre_bed_square_metres
from sim.ui.proto.capacity_remedies import capacity_remedies, render_remedies


def stub_game(trade_available=True, household_room=100.0):
    labour = types.SimpleNamespace(trade_available=lambda trade: trade_available, household_room=lambda: household_room)
    plans = {"coal": {"text": "dig it", "commands": ["quote mine coal 7", "buy mine coal 7"]}}
    return types.SimpleNamespace(
        HOURS_PER_PERSON_YEAR=2000.0, labour=labour,
        view=lambda name: lambda material, shortfall: plans.get(material, {"text": "wait", "commands": []}))


def trade_row(demand, supply, oversubscribed=True):
    return {"trade": "smith", "demand_hours_this_year": demand, "supply_hours_this_year": supply,
            "oversubscribed": oversubscribed, "projects_drawing_on_it": []}


# One row per short material: a surplus (no shortfall) has none, and each row carries the plan's commands.
rows = capacity_remedies(stub_game(), [{"material": "coal", "shortfall_t_per_yr": 7.0},
                                       {"material": "iron", "shortfall_t_per_yr": 0.0}], [])
check("only a material with a shortfall gets a remedy row", [row["shortage"] for row in rows] == ["coal"], rows)
check("a material row carries the plan's quote and buy commands",
      rows[0]["commands"] == ["quote mine coal 7", "buy mine coal 7"], rows)

# A trade short of hours: hire it (or train it when none can be hired), and house the hires when there is no room.
rows = capacity_remedies(stub_game(household_room=200.0), [], [trade_row(300000.0, 1000.0)])
check("an oversubscribed trade offers hiring enough people to cover the hours",
      rows[0]["commands"] == ["hire smith 150"], rows)
rows = capacity_remedies(stub_game(household_room=10.0), [], [trade_row(300000.0, 1000.0)])
check("...and housing for the hires the household has no room for",
      rows[0]["commands"] == ["hire smith 150", "buy housing 140"], rows)
rows = capacity_remedies(stub_game(trade_available=False), [], [trade_row(5000.0, 1000.0)])
check("a trade nobody offers is trained, not hired", rows[0]["commands"][0] == "train smith 2", rows)
check("a trade that is not oversubscribed gets no row",
      capacity_remedies(stub_game(), [], [trade_row(100.0, 1000.0, oversubscribed=False)]) == [], "row offered")

# The sizes that remedies suggest.
check("a mine is sized to the shortfall rounded up", mine_size_tonnes(6.2) == 7, mine_size_tonnes(6.2))
check("...and is never smaller than one tonne", mine_size_tonnes(0.0) == 1 and mine_size_tonnes(1e-12) == 1, "")
check("a shaft already being sunk counts against the shortfall",
      mine_shortfall_after_sinking("coal", 10.0, [["coal", 4.0, 1305.0], ["coal", 2.0, 1302.0], ["tin", 9.0, 1300.0]])
      == (6.0, 1302, 4.0), mine_shortfall_after_sinking("coal", 10.0, [["coal", 4.0, 1305.0], ["coal", 2.0, 1302.0]]))
check("...and with nothing being sunk the shortfall stands",
      mine_shortfall_after_sinking("coal", 10.0, [["tin", 9.0, 1300.0]]) == (0.0, None, 10.0), "")
check("a nitre bed covers the deficit with headroom, in whole hundreds of square metres",
      nitre_bed_square_metres(3.0, 1.2, 0.001) == 3600 and nitre_bed_square_metres(0.0, 1.2, 0.001) == 100,
      (nitre_bed_square_metres(3.0, 1.2, 0.001), nitre_bed_square_metres(0.0, 1.2, 0.001)))

# The rendering.
text = "\n".join(render_remedies([{"shortage": "coal", "short": "7 t/year", "commands": ["buy mine coal 7"], "how": "x"}]))
check("the rendered remedies show the commands under the shortage", "coal (short 7 t/year): buy mine coal 7" in text, text)  # presentation: wording of the screen
check("no remedies render nothing", render_remedies([]) == [], "")
