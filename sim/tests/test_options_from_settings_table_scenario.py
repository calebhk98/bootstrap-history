"""SCENARIO: the main menu's Options screen, driven through the CLI in process, is generated from the settings table
and saves what is set on it (Complaint 363). The table, the `options` command and the dice are rule tests in
`test_options_from_settings_table`."""
from .harness import *  # noqa: F401,F403
from sim.tests import cli_in_process
from sim.engine import settings as _settings
from sim.engine import settings_table as _table

QUICK_TOPIC = True

_scratch = tempfile.mkdtemp()


def _menu(keystrokes, name):
    config = os.path.join(_scratch, name + ".json")
    env = dict(os.environ, ROME_SIM_CONFIG=config, ROME_SAVE_DIR=os.path.join(_scratch, name))
    done = cli_in_process.run([], input_text=keystrokes, environment=env)
    saved = json.load(open(config)) if os.path.exists(config) else {}
    return done.stdout, saved


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
