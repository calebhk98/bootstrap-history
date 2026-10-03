"""seed_saved_both_modes: a saved and loaded `play` or `agent` game reports the seed it started with.

Complaints/360. Word seeds are kept as the word, number seeds as the number.
"""
from .harness import *  # noqa: F401,F403
from sim.engine.saveload import load_state

_scratch = tempfile.mkdtemp()
_SIMULATOR = os.path.join(HERE, "simulator.py")


def _start(mode, seed, name):
    path = os.path.join(_scratch, name + ".json")
    env = dict(os.environ, ROME_SAVE_DIR=_scratch, ROME_SIM_CONFIG=os.path.join(_scratch, "c.json"))
    text = '{"cmd":"state"}\n' if mode == "agent" else "quit\n"
    subprocess.run([sys.executable, _SIMULATOR, mode, "--civ", "rome_100ad",
                    "--seed", str(seed), "--session", path],
                   input=text, capture_output=True, text=True, timeout=120, env=env)
    return path


for _mode in ("play", "agent"):
    for _seed, _expected in ((7, 7), ("Dragon", "dragon")):
        _path = _start(_mode, _seed, "%s-%s" % (_mode, _seed))
        _loaded = sim()
        _loaded.seed = None
        try:
            load_state(_loaded, _path)
        except Exception as error:  # a missing save fails the check below
            _loaded.seed = "load failed: %s" % error
        check("%s game: a saved and loaded game reports seed %r" % (_mode, _seed),
              _loaded.seed == _expected, _loaded.seed)
