"""Regression coverage for complaints 250 (fresh seed per new game), 259 (menu
and play agree on goal and civilisations), 246 (save browser reads the nested
save), 204 (typed save accepts absolute paths) and 205 (changes window counts
from the arrival year)."""
from .harness import *
from sim.engine import settings as _settings
from sim.engine.saveload import goal_of_blob

_SIMULATOR = os.path.join(HERE, "simulator.py")
_scratch = tempfile.mkdtemp()


def _env(name):
    saves = os.path.join(_scratch, name)
    os.makedirs(saves, exist_ok=True)
    config_file = os.path.join(_scratch, name + "-config.json")
    env = dict(os.environ, ROME_SAVE_DIR=saves, ROME_SIM_CONFIG=config_file)
    env.pop("ROME_DEFAULT_SEED", None)
    return saves, env


def _run(arguments, text, env):
    return subprocess.run([sys.executable, _SIMULATOR] + arguments, input=text,
                          capture_output=True, text=True, timeout=120, env=env)


def _saves_in(saves):
    return [path for path in glob.glob(os.path.join(saves, "*.json"))
            if not path.endswith(".meta.json")]


# ---- 254: a fresh seed per new game, shown and recorded; --seed reproduces ----
_seen_seeds = []
for _index in range(2):
    _saves, _env_fresh = _env("fresh%d" % _index)
    _path = os.path.join(_saves, "g.json")
    _out = _run(["play", "--civ", "rome_100ad", "--session", _path], "quit\n", _env_fresh).stdout
    _match = re.search(r"[Ss]eed:? (\d+)", _out)
    _seen_seeds.append(int(_match.group(1)) if _match else None)
    _recorded = json.load(open(_path)).get("_seed")
    check("254: a new game without --seed prints its seed and records the same one",
          _match is not None and _recorded == _seen_seeds[-1], (_out[-400:], _recorded))
check("254: two new games without --seed draw different seeds",
      None not in _seen_seeds and _seen_seeds[0] != _seen_seeds[1], _seen_seeds)
_saves, _env_given = _env("given")
_path = os.path.join(_saves, "g.json")
_out = _run(["play", "--civ", "rome_100ad", "--seed", "7", "--session", _path],
            "quit\n", _env_given).stdout
check("254: --seed N is used, shown and recorded",
      re.search(r"[Ss]eed:? 7\b", _out) and json.load(open(_path)).get("_seed") == 7,
      _out[-400:])
_saves, _env_menu_seed = _env("menuseed")
_run(["menu"], "1\n" + "\n" * 12 + "quit\n", _env_menu_seed)
_menu_saves = _saves_in(_saves)
check("254: the new-game menu does not hard-code seed 1",
      len(_menu_saves) == 1 and json.load(open(_menu_saves[0])).get("_seed") not in (None, 1),
      [json.load(open(path)).get("_seed") for path in _menu_saves])

# ---- 263: the menu lists what play plays ----------------------------------------
_saves, _env_goal = _env("goal")
_menu = _run(["menu"], "1\n" + "\n" * 12 + "quit\n", _env_goal).stdout
check("263: the menu goal list offers the point-contact transistor",
      "oint-contact" in _menu, _menu[-1500:])
check("263: the menu no longer calls the 1951 transistor the default",
      "transistor (1951) is the original target and still the default" not in _menu, _menu[-1500:])
_menu_saves = _saves_in(_saves)
check("263: an all-defaults menu game aims at the goal `play` aims at by default",
      len(_menu_saves) == 1
      and goal_of_blob(json.load(open(_menu_saves[0]))) == "point_contact_transistor",
      [goal_of_blob(json.load(open(path))) for path in _menu_saves])
_civs_listing = _run(["civs"], "", _env_goal).stdout
_civ_ids = [line.split()[0] for line in _civs_listing.splitlines()
            if line and not line.startswith((" ", "starting")) and "," in line]
_offered = re.search(r"Which one\? \[1-(\d+)", _menu)
check("263: the menu offers as many civilisations as `civs` lists",
      _offered is not None and int(_offered.group(1)) == len(_civ_ids),
      (_offered and _offered.group(0), _civ_ids))

# ---- 250: the save browser reads the nested save ------------------------------
_saves, _env_list = _env("list")
_path = os.path.join(_saves, "r1.json")
_run(["play", "--civ", "rome_100ad", "--seed", "1", "--session", _path], "step 2\nquit\n", _env_list)
_rows = _settings.list_saves(_saves)
_row = _rows[0] if _rows else {}
check("250: list_saves reports the year a played save is at",
      bool(_row.get("year")) and _row.get("year") == json.load(open(_path))["scenario"]["year"], _row)
check("250: list_saves reports capital and founder status",
      isinstance(_row.get("capital"), (int, float)) and _row.get("founder_alive") is True, _row)
check("250: list_saves reports the goal",
      _row.get("goal") == "point_contact_transistor", _row)
with open(os.path.join(_saves, "broken.json"), "w") as _handle:
    _handle.write("{not json")
_broken = [row for row in _settings.list_saves(_saves) if row["filename"] == "broken.json"]
check("250: an unparseable file is listed as unreadable rather than skipped or zeroed",
      len(_broken) == 1 and _broken[0]["readable"] is False, _broken)

# ---- 208: typed save takes an absolute path -----------------------------------
_saves, _env_save = _env("save")
_target = os.path.join(_scratch, "exported.json")
_out = _run(["play", "--civ", "rome_100ad", "--seed", "1", "--session",
             os.path.join(_saves, "g.json")], "save %s\nquit\n" % _target, _env_save).stdout
check("208: `save /absolute/path.json` writes the file when typed by a player",
      os.path.exists(_target), _out[-400:])
_agent_refusal = S._agent_dispatch(sim(), NODES, {"cmd": "save", "file": _target + "2"})
check("208: the JSON protocol still refuses an absolute path",
      _agent_refusal.get("ok") is False and not os.path.exists(_target + "2"), _agent_refusal)

# ---- 209: changes counts the arrival year -------------------------------------
_saves, _env_changes = _env("changes")
_out = _run(["play", "--civ", "england_1300", "--seed", "1", "--session",
             os.path.join(_saves, "g.json")], "step 10\nchanges 10\nquit\n", _env_changes).stdout
check("209: `changes 10` ten years into a run is answered, not refused",
      "only goes back" not in _out, _out[-600:])
