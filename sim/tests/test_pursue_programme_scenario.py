"""SMOKE: pursue and programme on an unopened game. Pursue starts only what is on the goal's route, within the rush caps, and a
preview changes nothing; a programme persists across save and load (its year is test_pursue_programme). The route, caps, pause conditions
and handlers are in test_pursue_programme."""
from .harness import *  # noqa: F401,F403
from sim.engine.ui_port import closure
from sim.ui.memory import load_state, save_state


def _run(sim_state, **command):
    return S._agent_dispatch(sim_state, NODES, command)


game = unopened_sim(capital=20000.0)
game.end_year = game.cfg["start_year"] + 50
route = closure(NODES, GOAL)
_preview = _run(game, cmd="pursue", preview=True, limit=50)
check("pursue preview works", _preview.get("ok") and _preview.get("preview"), _preview)
_would = [row["id"] for row in _preview.get("would_start", [])]
check("pursue preview starts only route members", _would and all(node_id in route for node_id in _would), _would)
check("pursue preview changes nothing", not game.state.projects.active, sorted(game.state.projects.active))

_capped = _run(game, cmd="pursue", max_total_cost=1500.0, limit=50)
check("pursue obeys rush caps", sum(row["cost"] for row in _capped["started"]) <= 1500.0 + 1e-6, _capped)
check("pursue starts only route members", all(node_id in route for node_id in game.state.projects.active), sorted(game.state.projects.active))

# --- a programme persists across save and load and acts in the next step
_set = _run(game, cmd="programme", action="set", target=GOAL, max_annual_draw=400.0, limit=50)
check("programme set", _set.get("ok") and _set["programme"]["caps"].startswith("max_annual_draw"), _set)
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "game.json")
    save_state(game, path)
    _run(game, cmd="programme", action="clear")
    check("programme cleared", _run(game, cmd="programme")["programme"] is None)
    load_state(game, path)
check("programme survives save and load", _run(game, cmd="programme")["programme"] is not None)

