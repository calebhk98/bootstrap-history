"""Regression coverage for the new-game menu's seed question (blank draws a
random seed, a number is used, settings may hold a default) and for `goals`
agreeing with the menu's goal list (complaint 259)."""
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
_seed, _out = _seed_after_menu("word", "Rome42")
check("menu: a word seed is accepted and kept as typed, in lower case",
      _seed == "rome42", (_seed, _out[-800:]))
_seed, _out = _seed_after_menu("bad", "two words\n77")
check("menu: a seed with a space is asked again", _seed == 77, (_seed, _out[-800:]))
_seed, _out = _seed_after_menu("configured", "", {"default_seed": 9001})
check("menu: a blank answer takes the seed set in settings", _seed == 9001, (_seed, _out[-800:]))

# ---- a word seed replays the same game from the command line
_saves_word, _env_word = _env("word-replay")
def _word_game(name, seed):
    session = os.path.join(_saves_word, name + ".json")
    out = _run(["play", "--civ", "rome_100ad", "--seed", seed, "--session", session],
               "step 3\nstate\nquit\n", _env_word).stdout
    # "(took N s)" timing lines differ between runs; the game itself must not
    return "\n".join(line for line in out.split("Seed:", 1)[-1].splitlines()
                     if not line.strip().startswith("(took "))
_first, _second = _word_game("a", "hello"), _word_game("b", "hello")
check("--seed takes a word and prints it back", _first.startswith(" hello"), _first[:200])
check("the same word seed replays the same game", _first == _second.replace("b.json", "a.json"),
      (_first[:400], _second[:400]))
check("a different word seed rolls different dice",
      _word_game("c", "goodbye").split("\n", 1)[-1] != _first.split("\n", 1)[-1])

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
_snapshot_before = open(_snapshot).read()
_resume = _run(["play", "--session", _snapshot], "step 1\nquit\n", _env_export, _workdir).stdout
check("208: resuming a manually saved file does not overwrite it",
      "stays exactly as it is" in _resume and open(_snapshot).read() == _snapshot_before,
      _resume[-500:])
