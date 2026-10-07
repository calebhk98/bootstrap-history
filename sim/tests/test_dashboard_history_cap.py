"""Dashboard history capping: test the per-game option to keep only recent years."""
from .harness import *
from sim.engine.state import SimulationState, HouseholdState, ProjectsState, ScenarioState
import sim.engine.ui_port as ui_port

# Test 1: Default value is None (no cap).
state = SimulationState(household=HouseholdState(capital=1000),
                        projects=ProjectsState(),
                        scenario=ScenarioState())
check("default dashboard_history_years is None (no cap)",
      state.scenario.dashboard_history_years is None,
      state.scenario.dashboard_history_years)

# Test 2: Can set the option to a positive integer.
state.scenario.dashboard_history_years = 5
check("can set dashboard_history_years to positive integer",
      state.scenario.dashboard_history_years == 5,
      state.scenario.dashboard_history_years)

# Test 3: Trimming function works correctly.
hist = [{"year": i, "capital": i * 100} for i in range(100, 110)]
sim_obj = sim(capital=100_000)
sim_obj.state.scenario.dashboard_history_years = 3

from sim.ui.proto.dispatch import _trim_dashboard_history
_trim_dashboard_history(sim_obj, hist)
check("trim_dashboard_history keeps only most recent N entries",
      len(hist) == 3 and hist[0]["year"] == 107,
      {"len": len(hist), "years": [h["year"] for h in hist]})

# Test 4: Trimming works when cap is larger than history.
hist_small = [{"year": 100}, {"year": 101}]
sim_obj.state.scenario.dashboard_history_years = 10
_trim_dashboard_history(sim_obj, hist_small)
check("trim_dashboard_history preserves history when cap is larger",
      len(hist_small) == 2,
      len(hist_small))

# Test 5: Trimming does nothing when cap is None.
hist_uncapped = [{"year": i} for i in range(100, 110)]
sim_obj.state.scenario.dashboard_history_years = None
_trim_dashboard_history(sim_obj, hist_uncapped)
check("trim_dashboard_history does nothing when dashboard_history_years is None",
      len(hist_uncapped) == 10,
      len(hist_uncapped))

# Test 6: Save and load preserves the option.
import tempfile
import os
test_sim_save = sim(capital=100_000)
test_sim_save.state.scenario.dashboard_history_years = 7
with tempfile.TemporaryDirectory() as tmpdir:
    save_path = os.path.join(tmpdir, "test_game.json")
    S.save_state(test_sim_save, save_path)
    test_sim_loaded = sim(capital=100_000)
    S.load_state(test_sim_loaded, save_path)
    check("save/load preserves dashboard_history_years option",
          test_sim_loaded.state.scenario.dashboard_history_years == 7,
          test_sim_loaded.state.scenario.dashboard_history_years)

# Test 7: game_options command exists and can list options.
test_sim_cmd = sim(capital=100_000)
test_sim_cmd.state.scenario.dashboard_history_years = 5
reply_list = S._agent_dispatch(test_sim_cmd, NODES, {"cmd": "game_options"})
check("game_options command lists current value",
      reply_list["ok"] and reply_list["game_options"]["dashboard_history_years"] == 5,
      reply_list.get("game_options"))

# Test 8: game_options command can set dashboard_history_years to integer.
test_sim_cmd2 = sim(capital=100_000)
reply = S._agent_dispatch(test_sim_cmd2, NODES,
                         {"cmd": "game_options", "set": {"dashboard_history_years": 10}})
check("game_options command sets dashboard_history_years to integer",
      reply["ok"] and test_sim_cmd2.state.scenario.dashboard_history_years == 10,
      {"ok": reply["ok"], "value": test_sim_cmd2.state.scenario.dashboard_history_years})
