"""options_from_settings_table: the options screens are generated from the settings table.

Complaint 363. Every key of settings.CONFIG_DEFAULTS has a description in
settings_table, the main menu's Options screen and the `agent` `options`
command are both generated from that table, and the settings that were once
flag- or file-only (commission display, default seed, events, deterministic)
are on them.
"""
import argparse

from .harness import *  # noqa: F401,F403
from sim.engine import settings as _settings
from sim.engine import settings_table as _table

_scratch = tempfile.mkdtemp()
_SIMULATOR = os.path.join(HERE, "simulator.py")


def _menu(keystrokes, name):
    config = os.path.join(_scratch, name + ".json")
    env = dict(os.environ, ROME_SIM_CONFIG=config, ROME_SAVE_DIR=os.path.join(_scratch, name))
    done = subprocess.run([sys.executable, _SIMULATOR], input=keystrokes, capture_output=True,
                          text=True, timeout=120, env=env)
    saved = json.load(open(config)) if os.path.exists(config) else {}
    return done.stdout, saved


# --- the table covers every setting, and nothing else
check("every setting has a description in the settings table",
      not _table.undescribed(), _table.undescribed())
check("the table names no setting that does not exist",
      set(_table.SETTINGS) <= set(_settings.CONFIG_DEFAULTS),
      set(_table.SETTINGS) - set(_settings.CONFIG_DEFAULTS))
for _key in ("commission_display", "default_seed", "default_events", "default_deterministic"):
    check("%s is a setting" % _key, _key in _settings.CONFIG_DEFAULTS)

# --- the main menu lists every setting, and says which apply only at game start
_screen, _ = _menu("3\nb\nq\n", "screen")
_missing = [key for key, spec in _table.SETTINGS.items() if spec.label not in _screen]
check("the main-menu Options screen lists every setting", not _missing, (_missing, _screen[-1500:]))
_fog_line = [line for line in _screen.splitlines() if "fog of war" in line]
check("a game-start setting is shown and says it applies when a game starts",
      _fog_line and "game starts" in " ".join(_fog_line), _fog_line)

# --- the new ones can be changed from the menu
_number = {key: index + 1 for index, key in enumerate(_table.SETTINGS)}
_, _saved = _menu("3\n%d\nready\nb\nq\n" % _number["commission_display"], "commission")
check("commission display can be set from the menu",
      _saved.get("commission_display") == "ready", _saved)
_, _saved = _menu("3\n%d\ndragon\nb\nq\n" % _number["default_seed"], "seed")
check("a default seed (a word) can be set from the menu",
      _saved.get("default_seed") == "dragon", _saved)
_, _saved = _menu("3\n%d\nn\nb\nq\n" % _number["default_events"], "events")
check("events can be turned off from the menu", _saved.get("default_events") is False, _saved)
_, _saved = _menu("3\n%d\ny\nb\nq\n" % _number["default_deterministic"], "deterministic")
check("deterministic mode can be turned on from the menu",
      _saved.get("default_deterministic") is True, _saved)

# --- a throwaway setting appears on the screen with no menu edit
_settings.CONFIG_DEFAULTS["zz_probe"] = 3
_table.SETTINGS["zz_probe"] = _table.Setting(
    label="zz probe setting", description="Exists only for this test.", kind="count")
try:
    _lines = "\n".join(_table.screen_lines(dict(_settings.CONFIG_DEFAULTS)))
    check("a new setting appears on the generated screen", "zz probe setting" in _lines, _lines)
finally:
    del _settings.CONFIG_DEFAULTS["zz_probe"], _table.SETTINGS["zz_probe"]

# --- `agent` has an options command, from the same table
os.environ["ROME_SIM_CONFIG"] = os.path.join(_scratch, "agent.json")
_listing = S._agent_dispatch(sim(), NODES, {"cmd": "options"})
_listed = [row["key"] for row in _listing.get("options", [])]
check("agent `options` lists every setting", _listing.get("ok") and set(_listed) == set(_table.SETTINGS),
      (_listing.get("error"), _listed))
_set = S._agent_dispatch(sim(), NODES, {"cmd": "options", "set": "rows_per_page", "value": 12})
check("agent `options` sets a setting and saves it",
      _set.get("ok") and _settings.load_config()["rows_per_page"] == 12, _set)
_bad = S._agent_dispatch(sim(), NODES, {"cmd": "options", "set": "rows_per_page", "value": "many"})
check("...and refuses a value that does not fit", not _bad.get("ok") and "error" in _bad, _bad)
_unknown = S._agent_dispatch(sim(), NODES, {"cmd": "options", "set": "no_such", "value": 1})
check("...and an unknown setting", not _unknown.get("ok") and "error" in _unknown, _unknown)
_word = S._agent_dispatch(sim(), NODES, {"cmd": "options", "set": "default_seed", "value": "dragon"})
check("...and takes a seed word", _word.get("ok") and _settings.load_config()["default_seed"] == "dragon", _word)
_off = S._agent_dispatch(sim(), NODES, {"cmd": "options", "set": "default_events", "value": False})
check("...and a yes/no setting given as a JSON boolean",
      _off.get("ok") and _settings.load_config()["default_events"] is False, _off)

# --- events and deterministic reach a typed game
from sim.engine import cli_interactive as _play  # noqa: E402
from sim.engine.cli import DetRNG  # noqa: E402
_args = argparse.Namespace(strategy="recommended", goal=None, civ="rome_100ad", session=None,
                           horizon=100, seed=3, kit=None, mortal=False, fog=False, deterministic=False)
_play_sim = _play._play_build_sim(_args)[0]
check("play honours default_events off", _play_sim.events is False, _play_sim.events)
_settings.save_config(dict(_settings.load_config(), default_events=True, default_deterministic=True))
_play_sim = _play._play_build_sim(_args)[0]
check("play honours default_events on and default_deterministic",
      _play_sim.events is True and isinstance(_play_sim.rng, DetRNG), type(_play_sim.rng))
os.environ.pop("ROME_SIM_CONFIG", None)
