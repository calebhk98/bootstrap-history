"""demography_history: the shock and recovery rules are called with records built here and the screen is rendered from a
built reply; the screen's last year from the record is test_demography_screen_last_year."""
QUICK_TOPIC = True
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state, save_state
from sim.ui.proto.demography_history import recent_shocks, recovery
from sim.ui.proto.render_typed import render_pretty as _render_pretty

# --- shock history and recovery trajectory, from a built yearly record
record = [{"year": 140 + i, "population": value, "births": 0, "deaths": 10 * i, "nutrition_ratio": 1.0}
          for i, value in enumerate([1000, 1010, 1020, 800, 820, 840, 860, 880, 900, 920])]
shocks = recent_shocks(record)
check("a year the population fell sharply is listed as a shock",
      [row["year"] for row in shocks] == [143] and abs(shocks[0]["change_share"] + 0.2157) < 0.001, shocks)
check("...with that year's deaths and nutrition", shocks[0]["deaths"] == 30 and shocks[0]["nutrition_ratio"] == 1.0)
check("a fall under the shock threshold is not a shock",
      recent_shocks([{"year": 1, "population": 1000}, {"year": 2, "population": 980}]) == [])
check("a record of nothing, or of one year, has no shock", recent_shocks([]) == [] and recent_shocks(record[:1]) == [])
reading = recovery(record, 920, 150)
check("recovery names the peak, the gap to it and years since",
      reading["peak_population"] == 1020 and reading["peak_year"] == 142 and reading["years_since_peak"] == 8
      and abs(reading["share_below_peak"] - round(1.0 - 920 / 1020, 4)) < 1e-9, reading)
check("recovery projects years to regain the peak at the recent growth rate",
      reading["years_to_regain_peak_at_recent_rate"] is not None and reading["years_to_regain_peak_at_recent_rate"] > 0,
      reading)
check("a population back at its peak has no years to regain", recovery(record, 1020, 150)[
    "years_to_regain_peak_at_recent_rate"] == 0.0)
falling = [{"year": 100 + i, "population": 1000 - 50 * i} for i in range(6)]
check("a population that is still falling has no projected recovery",
      recovery(falling, 750, 105)["years_to_regain_peak_at_recent_rate"] is None)
check("no record, no recovery reading", recovery([], 100, 5) is None)

# presentation: the demography screen prints shock and recovery sections from a built reply
screen = {"population": 920, "cohorts": {"children": 300, "working_age": 600, "elderly": 20}, "working_age_share": 0.65,
          "last_year": None, "disease_burden": 0.5, "wage_index": 1.0, "epidemics_under_way": [],
          "recent_shocks": shocks, "recovery": reading, "trades": [], "not_held": []}
check("the screen prints shocks and recovery",
      "SHOCK" in _render_pretty("demography", screen) and "RECOVERY" in _render_pretty("demography", screen))

