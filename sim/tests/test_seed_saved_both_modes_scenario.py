"""Scenario for Complaint 360: a saved and loaded `play` or `agent` game started through the CLI reports the seed it started
with. The seed rules are in test_seed_saved_both_modes."""
from .harness import *  # noqa: F401,F403
from sim.tests import cli_in_process
from sim.engine.saveload import load_state

_scratch = tempfile.mkdtemp()


def _start(mode, seed, name):
    path = os.path.join(_scratch, name + ".json")
    env = dict(os.environ, ROME_SAVE_DIR=_scratch, ROME_SIM_CONFIG=os.path.join(_scratch, "c.json"))
    text = '{"cmd":"state"}\n' if mode == "agent" else "quit\n"
    cli_in_process.run([mode, "--civ", "rome_100ad", "--seed", str(seed), "--session", path],
                       input_text=text, environment=env)
    return path


for _mode in ("play", "agent"):
    for _seed, _expected in ((7, 7), ("Dragon", "dragon")):
        _path = _start(_mode, _seed, "%s-%s" % (_mode, _seed))
        _loaded = unopened_sim()
        _loaded.seed = None
        try:
            load_state(_loaded, _path)
        except Exception as error:  # a missing save fails the check below
            _loaded.seed = "load failed: %s" % error
        check("%s game: a saved and loaded game reports seed %r" % (_mode, _seed),
              _loaded.seed == _expected, _loaded.seed)
