"""demography_history: regression checks, run with `--only demography_history`."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.engine.proto.saveload import load_state, save_state
from sim.engine.proto.render_typed import render_pretty as _render_pretty


def _demography(game):
    return S._agent_dispatch(game, NODES, {"cmd": "demography"})


game = sim()
for _ in range(3):
    game.step()
record = game.state.population.yearly_record
flows = game._last_demographic_step
check("each step appends a yearly population record", len(record) == 3, record)
check("the latest record holds that step's births and deaths",
      record[-1]["births"] == round(flows.births) and record[-1]["deaths"] == round(flows.deaths), record[-1])

# a loaded game still shows last year's births and deaths
with tempfile.TemporaryDirectory(dir=os.getcwd()) as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    loaded = sim()
    load_state(loaded, path)
check("a loaded game keeps the yearly record", loaded.state.population.yearly_record == record,
      loaded.state.population.yearly_record)
loaded._last_demographic_step = None
_last = _demography(loaded)["last_year"]
check("...and shows last year's births from it", _last is not None and _last["births"] == round(flows.births), _last)

# shock history and recovery trajectory
shocked = sim()
shocked.year = 150
shocked.state.population.yearly_record = [
    {"year": 140 + i, "population": value, "births": 0, "deaths": 0, "nutrition_ratio": 1.0}
    for i, value in enumerate([1000, 1010, 1020, 800, 820, 840, 860, 880, 900, 920])]
shocked.population.children, shocked.population.working_age, shocked.population.elderly = 300.0, 600.0, 20.0
reply = _demography(shocked)
check("a year the population fell sharply is listed as a shock",
      [row["year"] for row in reply["recent_shocks"]] == [143]
      and abs(reply["recent_shocks"][0]["change_share"] + 0.2157) < 0.001, reply.get("recent_shocks"))
recovery = reply["recovery"]
check("recovery names the peak, the gap to it and years since",
      recovery["peak_population"] == 1020 and recovery["peak_year"] == 142
      and recovery["years_since_peak"] == 8, recovery)
check("recovery projects years to regain the peak at the recent growth rate",
      recovery["years_to_regain_peak_at_recent_rate"] is not None
      and recovery["years_to_regain_peak_at_recent_rate"] > 0, recovery)
check("the screen prints shocks and recovery",
      "SHOCK" in _render_pretty("demography", reply) and "RECOVERY" in _render_pretty("demography", reply))
check("the not-held list no longer claims there is no recovery timeline",
      not any("recovery timeline" in line for line in reply["not_held"]), reply["not_held"])
