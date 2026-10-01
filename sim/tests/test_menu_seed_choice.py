"""Regression coverage for the new-game menu's seed question (blank draws a
random seed, a number is used, settings may hold a default) and for `goals`
agreeing with the menu's goal list (complaint 263)."""
from .harness import *

_SIMULATOR = os.path.join(HERE, "simulator.py")
_scratch = tempfile.mkdtemp()


def _env(name, config=None):
    saves = os.path.join(_scratch, name)
    os.makedirs(saves, exist_ok=True)
    config_file = os.path.join(_scratch, name + "-config.json")
    if config is not None:
        with open(config_file, "w") as handle:
            json.dump(config, handle)
    env = dict(os.environ, ROME_SAVE_DIR=saves, ROME_SIM_CONFIG=config_file)
    env.pop("ROME_DEFAULT_SEED", None)
    return saves, env


def _run(arguments, text, env, cwd=None):
    return subprocess.run([sys.executable, _SIMULATOR] + arguments, input=text,
                          capture_output=True, text=True, timeout=120, env=env, cwd=cwd)


def _seed_after_menu(name, seed_answer, config=None):
    saves, env = _env(name, config)
    # civilisation, opening, fog, fuzzy, kit, mortality, goal, horizon, then the seed
    result = _run(["menu"], "1\n" + "\n" * 7 + seed_answer + "\n" + "\n" * 4 + "quit\n", env)
    found = [path for path in glob.glob(os.path.join(saves, "*.json"))
             if not path.endswith(".meta.json")]
    seed = json.load(open(found[0])).get("_seed") if len(found) == 1 else None
    return seed, result.stdout


_seed, _out = _seed_after_menu("typed", "4242")
check("menu: the seed question is asked", "Seed" in _out, _out[-1500:])
check("menu: a typed seed is the game's seed", _seed == 4242, (_seed, _out[-800:]))
_seed, _out = _seed_after_menu("blank", "")
check("menu: a blank seed draws a random one", _seed not in (None, 4242), (_seed, _out[-800:]))
_seed, _out = _seed_after_menu("bad", "abc\n77")
check("menu: a non-number seed is asked again", _seed == 77, (_seed, _out[-800:]))
_seed, _out = _seed_after_menu("configured", "", {"default_seed": 9001})
check("menu: a blank answer takes the seed set in settings", _seed == 9001, (_seed, _out[-800:]))

# ---- 263: `goals` lists what the menu lists, default first, without the stale blurb
_saves, _env_goals = _env("goals")
_goals = _run(["goals"], "", _env_goals).stdout
check("goals: the default goal is the first row",
      len(_goals.splitlines()) > 2 and "<- DEFAULT" in _goals.splitlines()[2], _goals[:600])
check("goals: no blurb calls the junction transistor the original goal",
      "original goal" not in _goals.lower(), _goals[:1200])

# ---- 208: a typed save says where it landed, stays frozen on resume, says how to move it
_saves, _env_export = _env("export")
_live = os.path.join(_saves, "g.json")
_workdir = os.path.join(_scratch, "work")
os.makedirs(_workdir, exist_ok=True)
_snapshot = os.path.join(_workdir, "snap.json")
_out = _run(["play", "--civ", "rome_100ad", "--seed", "1", "--session", _live],
            "save snap.json\nquit\n", _env_export, _workdir).stdout
check("208: a typed relative save says the full path it landed at",
      _snapshot in _out, _out[-700:])
_after_save = _out.split("saved:")[-1]
check("208: it says the live session file is separate",
      "live" in _after_save and _live in _after_save, _out[-700:])
check("208: it says how to copy the save to another machine",
      "--session" in _after_save and "copy" in _after_save, _out[-700:])
_resume = _run(["play", "--session", _snapshot], "step 1\nquit\n", _env_export, _workdir).stdout
check("208: resuming a manually saved file does not overwrite it",
      "stays exactly as it is" in _resume and json.load(open(_snapshot)).get("year") == 100,
      _resume[-500:])
