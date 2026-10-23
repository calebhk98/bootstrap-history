"""The human front end's rules, each called on built inputs: --pretty leaves the JSON reply alone (cli_agent.emit_reply),
the New Game wizard's remembered answers (wizard_answers.remember_answers), where saves go (settings.resolve_save_dir),
the in-game options menu (cli_interactive._ingame_options on a stand-in game), the welcome that ties the kit to its
cash. The reply renderings are in test_pretty_render_built_replies."""
QUICK_TOPIC = True

import contextlib
import io
import random
import types
from unittest import mock

from .harness import *  # noqa: F401,F403

from sim.engine import settings
from sim.ui import cli_agent, cli_interactive
from sim.ui.wizard_answers import REMEMBERED_KEYS, remember_answers
from sim.engine.ui_port import money_text, STARTING_KITS


def captured(function, *arguments):
    """(stdout, stderr) text written by `function(*arguments)`."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        function(*arguments)
    return out.getvalue(), err.getvalue()


# --- --pretty: stdout is byte-for-byte what a plain run prints; the rendering goes to stderr
_reply = {"ok": True, "year": 100, "capital": 1234.5}
_plain_out, _plain_err = captured(cli_agent.emit_reply, _reply, "state", {}, False)
_pretty_out, _pretty_err = captured(cli_agent.emit_reply, _reply, "state", {}, True)
check("emit_reply writes the reply as one JSON line", json.loads(_plain_out) == _reply and _plain_out.count("\n") == 1, _plain_out)
check("--pretty leaves stdout byte-for-byte what a plain run prints", _pretty_out == _plain_out, (_plain_out, _pretty_out))
check("a plain run writes nothing to stderr and --pretty writes the rendering there",
      _plain_err == "" and _pretty_err.strip() != "", (_plain_err, _pretty_err))

# --- the wizard remembers its answers as the next defaults, and only those
_remembered = remember_answers({"display_width": 99, "rows_per_page": 5, "show_welcome": False},
                               "han_china_100ad", "merchant", "n", "n", "y", "goal_node", 321)
check("the wizard writes every answer under its default_ key",
      (_remembered["default_civ"], _remembered["default_kit"], _remembered["default_fog"],
       _remembered["default_fuzzy_estimates"], _remembered["default_mortal"], _remembered["default_goal"],
       _remembered["default_horizon"]) == ("han_china_100ad", "merchant", False, False, True, "goal_node", 321), _remembered)
check("...and leaves the application's own preferences as they were",
      (_remembered["display_width"], _remembered["rows_per_page"], _remembered["show_welcome"]) == (99, 5, False)
      and set(_remembered) - {"display_width", "rows_per_page", "show_welcome"} == set(REMEMBERED_KEYS), _remembered)
check("every remembered key is a default the settings table declares",
      all(key in settings.CONFIG_DEFAULTS for key in REMEMBERED_KEYS),
      [key for key in REMEMBERED_KEYS if key not in settings.CONFIG_DEFAULTS])

# --- where saves go: ROME_SAVE_DIR beats the config's save_dir, which beats the home default
_env_dir, _config_dir = tempfile.mkdtemp(), tempfile.mkdtemp()
with mock.patch.dict(os.environ, {settings.SAVE_DIR_ENV: _env_dir}):
    _from_env = settings.resolve_save_dir({"save_dir": _config_dir})
with mock.patch.dict(os.environ):
    os.environ.pop(settings.SAVE_DIR_ENV, None)
    _from_config = settings.resolve_save_dir({"save_dir": _config_dir})
    _from_default = settings.resolve_save_dir({}, ensure=False)
check("the save directory is ROME_SAVE_DIR first", _from_env == _env_dir, _from_env)
check("...then the config's save_dir", _from_config == _config_dir, _from_config)
check("...then the home default", _from_default == os.path.join(os.path.expanduser("~"), ".rome-saves"), _from_default)


# --- the in-game options menu, on a stand-in game and scripted answers
def options_game(immortal=True):
    return types.SimpleNamespace(
        cfg={"start_year": 100, "horizon_years": 500, "immortal": immortal}, civ={"id": "rome_100ad", "name": "Rome"},
        fog=False, fuzzy_estimates=False, year=130, end_year=600, rng=random.Random(1), life_left=None, founder_alive=True)


def run_options(game, session, *answers):
    """The session path _ingame_options hands back, with `answers` typed at its prompts."""
    with mock.patch("builtins.input", side_effect=list(answers)), contextlib.redirect_stdout(io.StringIO()), \
            mock.patch.object(cli_interactive, "save_state", lambda game_saved, path: open(path, "w").write("{}")):
        return cli_interactive._ingame_options(game, session)


_options_dir = tempfile.mkdtemp()
_session = os.path.join(_options_dir, "game.json")
_game = options_game()
run_options(_game, _session, "1", "250", "b")
check("changing the horizon moves the game's end year and horizon", (_game.end_year, _game.cfg["horizon_years"]) == (250, 150),
      (_game.end_year, _game.cfg["horizon_years"]))
check("...and writes the horizon to the save's sidecar so a resume keeps it",
      settings.load_session_meta(_session).get("horizon_years") == 150, settings.load_session_meta(_session))
_before = (_game.end_year, _game.cfg["horizon_years"])
run_options(_game, _session, "1", "125", "b")
check("an end year already past is refused and changes nothing", (_game.end_year, _game.cfg["horizon_years"]) == _before,
      (_game.end_year, _game.cfg["horizon_years"]))

_mortal_game = options_game()
run_options(_mortal_game, _session, "2", "y", "b")
check("turning mortality on makes the founder mortal with a lifespan left",
      _mortal_game.cfg["immortal"] is False and _mortal_game.life_left is not None and _mortal_game.life_left > 0,
      (_mortal_game.cfg, _mortal_game.life_left))
_declined_game = options_game()
run_options(_declined_game, _session, "2", "n", "b")
check("declining it leaves the founder immortal", _declined_game.cfg["immortal"] is True and _declined_game.life_left is None)

_moved_to = os.path.join(_options_dir, "elsewhere.json")
open(_session, "w").write("{}")
_returned = run_options(_game, _session, "3", _moved_to, "b")
check("moving a save hands back the new path, writes it there and removes the old file",
      _returned == _moved_to and os.path.exists(_moved_to) and not os.path.exists(_session), (_returned, os.listdir(_options_dir)))
check("...and carries the sidecar horizon with it",
      settings.load_session_meta(_moved_to).get("horizon_years") == 150 and not os.path.exists(_session + ".meta.json"),
      os.listdir(_options_dir))

# --- the welcome ties the kit's size to the cash it is worth, in the civilisation's own coin
_arrival = types.SimpleNamespace(capital=3000.0, civ=S.load_civ("han_china_100ad"), year=100, fog=False)
_welcome, _ = captured(cli_interactive._play_print_welcome, _arrival, "merchant")
_cash = money_text(_arrival.capital, _arrival)
_kit_years = "%.1f labourer-years" % STARTING_KITS["merchant"]["labourer_years"]
check("the arrival line and the kit line state the same cash, and the kit line its size in labourer-years",  # presentation: the welcome's wording
      ("arrive in 100 AD with %s" % _cash) in _welcome and _kit_years in _welcome and ("which here is %s" % _cash) in _welcome,
      _welcome[:400])
