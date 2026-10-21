"""Scenario (Complaint 640 audit): the new-game menu's seed question through the real CLI, word seeds replaying the same
game, and `goals` agreeing with the menu (complaint 259). The seed rules are tests in test_menu_seed_choice."""
import builtins

from .harness import *
from sim.tests import cli_in_process

from sim.tests import fingerprint as perf_fingerprint
from sim.ui import cli_interactive
from sim.engine.settings_table import normal_seed

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
    return cli_in_process.run(arguments, input_text=text, environment=env, cwd=cwd)


def _ask_seed(answers, config=None):
    """What the seed question returns for these typed answers, with settings `config`."""
    remaining = list(answers)
    real_input = builtins.input
    builtins.input = lambda prompt="": remaining.pop(0)
    try:
        return cli_interactive._new_game_ask_seed(config or {})
    finally:
        builtins.input = real_input


# ---- the whole menu, through the CLI: the question is asked and the typed seed is the game's seed
saves, env = _env("typed")
# civilisation, opening, fog, fuzzy, kit, mortality, goal, horizon, then the seed
menu_result = _run(["menu"], "1\n" + "\n" * 7 + "4242\n" + "\n" * 4 + "quit\n", env)
found = [path for path in glob.glob(os.path.join(saves, "*.json")) if not path.endswith(".meta.json")]
menu_seed = json.load(open(found[0])).get("_seed") if len(found) == 1 else None
check("menu: the seed question is asked", "Seed" in menu_result.stdout, menu_result.stdout[-1500:])
check("menu: a typed seed is the game's seed", menu_seed == 4242, (menu_seed, menu_result.stdout[-800:]))

# ---- a word seed replays the same game, a different word rolls different dice
def _word_game_digest(seed):
    game = S.Sim(NODES, ORDER, random.Random(normal_seed(seed)), events=True, manual=True,
                 civ=S.load_civ("rome_100ad"))
    game.goal, game.done_year = GOAL, {}
    game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
    seat = game.playing_seats()[0]
    with game.act_as(seat):    # the year's dice (the society's year, the hazards), without the market closing
        game.begin_seat_year()
        game.begin_world_year()
        game._step_staff()
        game._step_money_seat()
        game._step_money_world()
        game._step_dated_shocks([seat])
        game._run_seat_work()
        game._random_events(game.state.scenario.year, [seat])
    game.state.scenario.year += 1
    return perf_fingerprint.digest(perf_fingerprint.state_of(game))


hello_digest = _word_game_digest("hello")
check("the same word seed replays the same game", hello_digest == _word_game_digest("hello"),
      "two runs of hello differ")
check("a different word seed rolls different dice", hello_digest != _word_game_digest("goodbye"),
      "hello and goodbye match")

# ---- 263: `goals` lists what the menu lists, default first, without the stale blurb
_saves, _env_goals = _env("goals")
_goals = _run(["goals"], "", _env_goals).stdout
check("goals: the default goal is the first row",
      len(_goals.splitlines()) > 2 and "<- DEFAULT" in _goals.splitlines()[2], _goals[:600])
check("goals: no blurb calls the junction transistor the original goal",
      "original goal" not in _goals.lower(), _goals[:1200])

# ---- 208: a typed save says where it landed and stays frozen on resume; --seed takes a word and prints it back
_saves, _env_export = _env("export")
_live = os.path.join(_saves, "g.json")
_workdir = os.path.join(_scratch, "work")
os.makedirs(_workdir, exist_ok=True)
_snapshot = os.path.join(_workdir, "snap.json")
_out = _run(["play", "--civ", "rome_100ad", "--seed", "hello", "--session", _live],
            "save snap.json\nquit\n", _env_export, _workdir).stdout
check("--seed takes a word and prints it back", "hello" in _out, _out[:300])
check("208: a typed relative save says the full path it landed at", _snapshot in _out, _out[-700:])
_snapshot_before = open(_snapshot).read()
_resume = _run(["play", "--session", _snapshot], "start scientific_method\nquit\n", _env_export, _workdir).stdout
check("208: resuming a manually saved file does not overwrite it",
      "stays exactly as it is" in _resume and open(_snapshot).read() == _snapshot_before,
      _resume[-500:])
