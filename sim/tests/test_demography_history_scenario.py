"""SCENARIO (Complaint 640): a stepped game keeps a yearly record, a save carries it and the screen reads it back (the shock and recovery rules are in test_demography_history)."""
import os
import tempfile

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state, save_state
from sim.ui.proto.demography_history import recent_shocks, recovery
from sim.ui.proto.render_typed import render_pretty as _render_pretty


def _demography(game):
    return S._agent_dispatch(game, NODES, {"cmd": "demography"})

# --- SCENARIO: a stepped game keeps a yearly record, a save carries it, and the screen reads it back
game = sim()
for _ in range(2):
    game.step()
yearly = game.state.population.yearly_record
flows = game._last_demographic_step
check("scenario: each step appends a yearly population record holding that step's births and deaths",
      len(yearly) == 2 and yearly[-1]["births"] == round(flows.births) and yearly[-1]["deaths"] == round(flows.deaths),
      yearly)
with tempfile.TemporaryDirectory(dir=os.getcwd()) as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    loaded = sim()
    load_state(loaded, path)
check("scenario: a loaded game keeps the yearly record", loaded.state.population.yearly_record == yearly,
      loaded.state.population.yearly_record)
loaded._last_demographic_step = None
_last = _demography(loaded)["last_year"]
check("scenario: ...and shows last year's births from it", _last is not None and _last["births"] == round(flows.births),
      _last)
