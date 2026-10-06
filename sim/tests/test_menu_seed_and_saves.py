"""Regression coverage for complaints 250 (fresh seed per new game), 259 (menu
and play agree on goal and civilisations), 246 (save browser reads the nested
save), 204 (typed save accepts absolute paths) and 205 (changes window counts
from the arrival year)."""
from .harness import *
from sim.tests import cli_in_process
from sim.engine import settings as _settings

_scratch = tempfile.mkdtemp()


def _env(name):
    saves = os.path.join(_scratch, name)
    os.makedirs(saves, exist_ok=True)
    config_file = os.path.join(_scratch, name + "-config.json")
    env = dict(os.environ, ROME_SAVE_DIR=saves, ROME_SIM_CONFIG=config_file)
    env.pop("ROME_DEFAULT_SEED", None)
    return saves, env


def _run(arguments, text, env):
    return cli_in_process.run(arguments, input_text=text, environment=env)


def _saves_in(saves):
    return [path for path in glob.glob(os.path.join(saves, "*.json"))
            if not path.endswith(".meta.json")]


# ---- 254 and 250 and 208: one played game without --seed, stepped a year, saved to an absolute path ----
_saves, _env_fresh = _env("fresh")
_path = os.path.join(_saves, "g.json")
_target = os.path.join(_scratch, "exported.json")
_out = _run(["play", "--civ", "rome_100ad", "--session", _path], "step 1\nsave %s\nquit\n" % _target, _env_fresh).stdout
_match = re.search(r"[Ss]eed:? (\d+)", _out)
_play_seed = int(_match.group(1)) if _match else None
_recorded = json.load(open(_path)).get("_seed")
check("254: a new game without --seed prints its seed and records the same one",
      _match is not None and _recorded == _play_seed, (_out[-400:], _recorded))
check("208: `save /absolute/path.json` writes the file when typed by a player",
      os.path.exists(_target), _out[-400:])
_agent_refusal = S._agent_dispatch(sim(), NODES, {"cmd": "save", "file": _target + "2"})
check("208: the JSON protocol still refuses an absolute path",
      _agent_refusal.get("ok") is False and not os.path.exists(_target + "2"), _agent_refusal)
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

_saves, _env_given = _env("given")
_path = os.path.join(_saves, "g.json")
_out = _run(["play", "--civ", "rome_100ad", "--seed", "7", "--session", _path],
            "quit\n", _env_given).stdout
check("254: --seed N is used, shown and recorded",
      re.search(r"[Ss]eed:? 7\b", _out) and json.load(open(_path)).get("_seed") == 7,
      _out[-400:])

# ---- 254 and 263: the menu draws a fresh seed and lists what play plays ----
_saves, _env_menu = _env("menu")
_menu = _run(["menu"], "1\n" + "\n" * 12 + "quit\n", _env_menu).stdout
_menu_saves = _saves_in(_saves)
_menu_record = json.load(open(_menu_saves[0])) if len(_menu_saves) == 1 else {}
check("254: the new-game menu draws its own seed, not a fixed one and not play's",
      _menu_record.get("_seed") not in (None, 1, _play_seed), (_menu_record.get("_seed"), _play_seed))
check("263: the menu goal list offers the point-contact transistor",
      "oint-contact" in _menu, _menu[-1500:])
check("263: an all-defaults menu game aims at the goal `play` aims at by default",
      _menu_record.get("_goal") == "point_contact_transistor", _menu_record.get("_goal"))
_offered = re.search(r"Which one\? \[1-(\d+)", _menu)
check("263: the menu offers as many civilisations as exist",
      _offered is not None and int(_offered.group(1)) == len(S.civilization_ids()),
      (_offered and _offered.group(0), S.civilization_ids()))

# ---- 205: `changes` counts the arrival year as part of the record ----
_changes_game = sim()
_changes_game.end_year = _changes_game.cfg["start_year"] + 50
S._agent_dispatch(_changes_game, NODES, {"cmd": "step", "years": 1})
_changes_reply = S._agent_dispatch(_changes_game, NODES, {"cmd": "changes", "years": 1})
check("205: `changes 1` one year in is answered, not refused", _changes_reply.get("ok") is True, _changes_reply)
