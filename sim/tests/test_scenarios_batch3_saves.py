"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenarios: games saved and played on.

The rules have tests of their own: test_complaint_181_save_cost (when a save is written),
test_complaint_188_fuzzy_estimates (the estimates) and test_fuzzy_estimates_saved_rule (the option survives a save).
What stays here is that a played game carries them: the play loop saves only what changed, and a refused `start`
states the real need."""
import io
import contextlib

from .harness import *  # noqa: F401,F403
from sim.engine.saveload import save_state, load_state
from sim.ui.cli_interactive import _play_run_one_command
from sim.ui.save_policy import SavePolicy


# ---- scenario 181: the play loop writes the save only when the game changed ----------------------------------------
class _CountReplaces:
    def __enter__(self):
        self.replaces = 0
        self._real_replace = os.replace

        def counting_replace(source, destination):
            self.replaces += 1
            return self._real_replace(source, destination)

        os.replace = counting_replace
        return self

    def __exit__(self, *exception):
        os.replace = self._real_replace


def _play(test_sim, command, path):
    with contextlib.redirect_stdout(io.StringIO()):
        _play_run_one_command(test_sim, NODES, command, path, SavePolicy(path))


_venture_game = sim(capital=1e9)
_venture_id = next(node_id for node_id in ORDER if _venture_game.is_venture(node_id))
run_it(_venture_game, _venture_id)
_session = os.path.join(tempfile.mkdtemp(), "session.json")
save_state(_venture_game, _session)
_venture_game.end_year = _venture_game.cfg["start_year"] + 500
_play(_venture_game, {"cmd": "state"}, _session)   # the first look sets a one-time flag
with _CountReplaces() as _counted:
    _play(_venture_game, {"cmd": "open", "id": _venture_id}, _session)
    _play(_venture_game, {"cmd": "open", "id": "no_such_node_anywhere"}, _session)
    _play(_venture_game, {"cmd": "state"}, _session)
check("scenario save cost: refusals and a bare state rewrite the save zero times", _counted.replaces == 0, _counted.replaces)
with _CountReplaces() as _counted:
    _play(_venture_game, {"cmd": "step", "years": 1}, _session)
_check_game = unopened_sim(capital=1.0)
load_state(_check_game, _session)
check("scenario save cost: a step rewrites the save once, and what it wrote is the stepped game",
      _counted.replaces == 1 and _check_game.state.scenario.year == _venture_game.state.scenario.year,
      (_counted.replaces, _check_game.state.scenario.year, _venture_game.state.scenario.year))


# ---- scenario 188: the estimates option survives a save, and `start` checks the real needs ---------------------------
NODE = "fin_lottery"          # a going concern with staff, a foreman-free crew and two hired trades


def _why_of(sim_state, node_id=NODE):
    return S._agent_dispatch(sim_state, NODES, {"cmd": "why", "id": node_id})


def _fuzzy_game():
    fuzzy = unopened_sim(capital=1_000_000)
    fuzzy.fuzzy_estimates = True
    return fuzzy


_refused_game = _fuzzy_game()
_refused = S._agent_dispatch(_refused_game, NODES, {"cmd": "start", "id": "ag2_botanic_garden"})
_real_art = NODES["ag2_botanic_garden"]["art"]
_need = "needs %d trained craftsmen" % _real_art
check("scenario fuzzy estimates: a refusal at start states the real need while why and the compact why do not print it",
      _refused.get("ok") is False and _need in _refused.get("error", "")
      and _need not in json.dumps(_why_of(_refused_game, "ag2_botanic_garden"))
      and _need not in json.dumps(S._agent_dispatch(_refused_game, NODES, {"cmd": "why", "id": "ag2_botanic_garden",
                                                                          "compact": True})), _refused)
