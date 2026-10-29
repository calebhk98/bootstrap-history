"""Dashboard history capping: the trim rule is called with a built state. The game_options command is in test_game_options_command.py."""
QUICK_TOPIC = True

from .harness import check
from sim.engine.state import SimulationState, HouseholdState, ProjectsState

state = SimulationState(household=HouseholdState(capital=1000),
                        projects=ProjectsState())

# Test 3: Trimming function works correctly.
hist = [{"year": i, "capital": i * 100} for i in range(100, 110)]
from types import SimpleNamespace
sim_obj = SimpleNamespace(state=state)   # the trim reads only the seat progress
sim_obj.state.seat_progress.dashboard_history_years = 3

from sim.ui.proto.dispatch import _trim_dashboard_history
_trim_dashboard_history(sim_obj, hist)
check("trim_dashboard_history keeps only most recent N entries",
      len(hist) == 3 and hist[0]["year"] == 107,
      {"len": len(hist), "years": [h["year"] for h in hist]})

# Test 4: Trimming works when cap is larger than history.
hist_small = [{"year": 100}, {"year": 101}]
sim_obj.state.seat_progress.dashboard_history_years = 10
_trim_dashboard_history(sim_obj, hist_small)
check("trim_dashboard_history preserves history when cap is larger",
      len(hist_small) == 2,
      len(hist_small))

# Test 5: Trimming does nothing when cap is None.
hist_uncapped = [{"year": i} for i in range(100, 110)]
sim_obj.state.seat_progress.dashboard_history_years = None
_trim_dashboard_history(sim_obj, hist_uncapped)
check("trim_dashboard_history does nothing when dashboard_history_years is None",
      len(hist_uncapped) == 10,
      len(hist_uncapped))
