"""Regression coverage for Complaint 195: fuzzy estimates are a normal game
option (new-game menu, in-game options screen, settings default, save) and
the README says `help commands` lists every command."""
from .harness import *
from sim.engine import settings as _settings

_SIMULATOR = os.path.join(HERE, "simulator.py")
_scratch = tempfile.mkdtemp()


def _env(name, config=None):
    saves = os.path.join(_scratch, name)
    os.makedirs(saves, exist_ok=True)
    config_file = os.path.join(_scratch, name + "-config.json")
    if config is not None:
        with open(config_file, "w") as handle:
            json.dump(config, handle)
    return saves, config_file, dict(os.environ, ROME_SAVE_DIR=saves, ROME_SIM_CONFIG=config_file)


def _run(arguments, text, env):
    return subprocess.run([sys.executable, _SIMULATOR] + arguments, input=text,
                          capture_output=True, text=True, timeout=120, env=env)


def _only_save(saves):
    found = glob.glob(os.path.join(saves, "*.json"))
    found = [path for path in found if not path.endswith(".meta.json")]
    return json.load(open(found[0])) if found else {}


def _fuzzy_in(blob):
    return [value for key, value in blob.items() if "fuzzy_estimates" in key]


# ---- settings default ---------------------------------------------------------
check("settings: a default for fuzzy estimates exists and is off",
      _settings.CONFIG_DEFAULTS.get("default_fuzzy_estimates") is False,
      _settings.CONFIG_DEFAULTS)

# ---- new-game menu offers it, and answering y starts a game with it on ---------
_saves, _config, _env_menu = _env("menu")
_menu = _run(["menu"], "1\n\n\ny\n" + "\n" * 8 + "quit\n", _env_menu)
check("menu: the new-game wizard asks about fuzzy estimates",
      "uzzy" in _menu.stdout, _menu.stdout[-1500:])
check("menu: a new game started with y has fuzzy estimates on in its save",
      _fuzzy_in(_only_save(_saves)) == [True], (_fuzzy_in(_only_save(_saves)), _menu.stdout[-800:]))

# ---- settings default applies when nothing else says otherwise -----------------
_saves, _config, _env_default = _env("default", {"default_fuzzy_estimates": True})
_run(["play", "--civ", "rome_100ad", "--session", os.path.join(_saves, "g.json")],
     "step 1\nquit\n", _env_default)
check("settings default on: a plain `play` starts with fuzzy estimates on",
      _fuzzy_in(_only_save(_saves)) == [True], _fuzzy_in(_only_save(_saves)))

_saves, _config, _env_plain = _env("plain")
_run(["play", "--civ", "rome_100ad", "--session", os.path.join(_saves, "g.json")],
     "step 1\nquit\n", _env_plain)
check("settings default off: a plain `play` starts with fuzzy estimates off",
      _fuzzy_in(_only_save(_saves)) == [False], _fuzzy_in(_only_save(_saves)))

_saves, _config, _env_flag = _env("flag")
_run(["play", "--civ", "rome_100ad", "--fuzzy-estimates",
      "--session", os.path.join(_saves, "g.json")], "step 1\nquit\n", _env_flag)
check("`play --fuzzy-estimates` still turns it on",
      _fuzzy_in(_only_save(_saves)) == [True], _fuzzy_in(_only_save(_saves)))

# a game begun without it is not switched on by the default when it is resumed
_saves, _config, _env_resume = _env("resume")
_path = os.path.join(_saves, "g.json")
_run(["play", "--civ", "rome_100ad", "--session", _path], "step 1\nquit\n", _env_resume)
with open(_config, "w") as handle:
    json.dump({"default_fuzzy_estimates": True}, handle)
_run(["play", "--session", _path], "step 1\nquit\n", _env_resume)
check("resuming a game started without fuzzy does not turn it on from the default",
      _fuzzy_in(_only_save(_saves)) == [False], _fuzzy_in(_only_save(_saves)))

# ---- the in-game options screen shows it, and it can be turned on there --------
_saves, _config, _env_opts = _env("options")
_path = os.path.join(_saves, "g.json")
_shown = _run(["play", "--civ", "rome_100ad", "--session", _path],
              "options\nb\nquit\n", _env_opts)
check("options screen shows fuzzy estimates (off)",
      re.search(r"fuzzy estimates\s*:\s*off", _shown.stdout) is not None, _shown.stdout[-1200:])
_turned = _run(["play", "--session", _path], "options\nf\ny\nb\nquit\n", _env_opts)
check("options screen can turn fuzzy estimates on mid-game",
      re.search(r"fuzzy estimates\s*:\s*on", _turned.stdout) is not None
      and _fuzzy_in(_only_save(_saves)) == [True], _turned.stdout[-1200:])
_again = _run(["play", "--session", _path], "options\nb\nquit\n", _env_opts)
check("save/load keeps fuzzy estimates: still on after a resume",
      re.search(r"fuzzy estimates\s*:\s*on", _again.stdout) is not None, _again.stdout[-1200:])

# ---- README ----------------------------------------------------------------------
_readme = open(os.path.join(ROOT, "README.md")).read()
_playing = _readme.split("## Playing", 1)[1].split("\n## ", 1)[0]
check("README: Playing says the table is a starting set and help commands lists every command",
      "starting set" in _playing and "`help commands` lists every command" in _playing
      and "`help <command>`" in _playing, _playing[:600])
check("README: fuzzy estimates are mentioned next to fog in the options list",
      "--fuzzy-estimates" in _readme.split("## Playing", 1)[0], "")
