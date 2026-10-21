"""SCENARIO: the dashboard history cap survives a save and load and is set and listed by the game_options command.
The trim rule is in test_dashboard_history_cap.py."""
from .harness import *

# Test 6: Save and load preserves the option.
import tempfile
import os
test_sim_save = sim(capital=100_000)
test_sim_save.state.seat_progress.dashboard_history_years = 7
with tempfile.TemporaryDirectory() as tmpdir:
    save_path = os.path.join(tmpdir, "test_game.json")
    S.save_state(test_sim_save, save_path)
    test_sim_loaded = sim(capital=100_000)
    S.load_state(test_sim_loaded, save_path)
    check("scenario: save/load preserves dashboard_history_years option",
          test_sim_loaded.state.seat_progress.dashboard_history_years == 7,
          test_sim_loaded.state.seat_progress.dashboard_history_years)

# SCENARIO (wiring): the game_options command sets the option and lists it back.
test_sim_cmd = sim(capital=100_000)
reply = S._agent_dispatch(test_sim_cmd, NODES, {"cmd": "game_options", "set": {"dashboard_history_years": 10}})
reply_list = S._agent_dispatch(test_sim_cmd, NODES, {"cmd": "game_options"})
check("scenario: game_options sets dashboard_history_years to an integer and lists the current value",
      reply["ok"] and test_sim_cmd.state.seat_progress.dashboard_history_years == 10
      and reply_list["ok"] and reply_list["game_options"]["dashboard_history_years"] == 10,
      {"ok": reply["ok"], "listed": reply_list.get("game_options")})
