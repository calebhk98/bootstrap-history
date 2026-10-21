"""options_from_settings_table: the options screens are generated from the settings table.

Complaint 363. Every key of settings.CONFIG_DEFAULTS has a description in
settings_table, the main menu's Options screen and the `agent` `options`
command are both generated from that table, and the settings that were once
flag- or file-only (commission display, default seed, events, deterministic)
are on them.
"""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.tests import cli_in_process
from sim.engine import settings as _settings
from sim.engine import settings_table as _table
from sim.engine.ui_port import DetRNG
from sim.ui.play_dice import dice_for_play
from sim.ui.proto.dispatch_options import _cmd_options

QUICK_TOPIC = True

_scratch = tempfile.mkdtemp()


def _menu(keystrokes, name):
    config = os.path.join(_scratch, name + ".json")
    env = dict(os.environ, ROME_SIM_CONFIG=config, ROME_SAVE_DIR=os.path.join(_scratch, name))
    done = cli_in_process.run([], input_text=keystrokes, environment=env)
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
check("the main-menu Options screen lists every setting",   # presentation: the screen is text
      not _missing, (_missing, _screen[-1500:]))
_fog_line = [line for line in _screen.splitlines() if "fog of war" in line]
check("a game-start setting is shown and says it applies when a game starts",   # presentation: the screen's wording
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
_saved_config_path = os.environ.get("ROME_SIM_CONFIG")
os.environ["ROME_SIM_CONFIG"] = os.path.join(_scratch, "agent.json")
_stand_in = SimpleNamespace(is_visible=lambda node_id: True)    # the handler ignores the game but for hiding technologies


def _options(**fields):
    return _cmd_options(_stand_in, {}, dict(cmd="options", **fields), False)


_listing = _options()
_listed = [row["key"] for row in _listing.get("options", [])]
check("agent `options` lists every setting", _listing.get("ok") and set(_listed) == set(_table.SETTINGS),
      (_listing.get("error"), _listed))
_set = _options(set="rows_per_page", value=12)
check("agent `options` sets a setting and saves it",
      _set.get("ok") and _settings.load_config()["rows_per_page"] == 12, _set)
_bad = _options(set="rows_per_page", value="many")
check("...and refuses a value that does not fit", not _bad.get("ok") and "error" in _bad, _bad)
_unknown = _options(set="no_such", value=1)
check("...and an unknown setting", not _unknown.get("ok") and "error" in _unknown, _unknown)
_word = _options(set="default_seed", value="dragon")
check("...and takes a seed word", _word.get("ok") and _settings.load_config()["default_seed"] == "dragon", _word)
_off = _options(set="default_events", value=False)
check("...and a yes/no setting given as a JSON boolean",
      _off.get("ok") and _settings.load_config()["default_events"] is False, _off)

if _saved_config_path is None:
    os.environ.pop("ROME_SIM_CONFIG", None)
else:
    os.environ["ROME_SIM_CONFIG"] = _saved_config_path

# --- events and deterministic reach a typed game's dice
_dice, _events = dice_for_play({"default_events": False}, False, 3)
check("play honours default_events off", _events is False and not isinstance(_dice, DetRNG), (_events, type(_dice)))
_dice, _events = dice_for_play({"default_events": True, "default_deterministic": True}, False, 3)
check("play honours default_events on and default_deterministic",
      _events is True and isinstance(_dice, DetRNG), (_events, type(_dice)))
_dice, _events = dice_for_play({}, True, 3)
check("the deterministic flag asks for the deterministic dice whatever is saved, and events default on",
      isinstance(_dice, DetRNG) and _events is True, (_events, type(_dice)))
