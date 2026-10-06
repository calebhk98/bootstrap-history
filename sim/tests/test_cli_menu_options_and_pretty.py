"""The human front end: the --pretty rendering, the main menu and New Game wizard, in-game and application options, and the screens as a player of each civilisation reads them."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent
from sim.tests import cli_in_process
from sim.ui.proto.render_typed import render_pretty as _render_pretty

# New work: a human-readable rendering (--pretty), the menu starting the game
# instead of describing how to, and `load` refusing a file that is not a
# save from this game.
# ============================================================================

def _run_agent(input_lines, extra_args=(), civ="rome_100ad", cwd=None):
    """Drive the real `agent` subcommand in-process (cli_in_process.py), optionally with
    extra CLI flags (--pretty among them). Returns (stdout, stderr, returncode)."""
    arguments = ["agent", "--civ", civ] + list(extra_args)
    proc = cli_in_process.run(arguments, input_text="\n".join(json.dumps(command) for command in input_lines) + "\n",
                              cwd=(cwd or ROOT))
    return proc.stdout, proc.stderr, proc.returncode


_PRETTY_CMDS = [{"cmd": "state"}, {"cmd": "why", "id": "blast_furnace"}, {"cmd": "money"}, {"cmd": "risk"},
                {"cmd": "quit"}]

# --- I/N: the one guarantee the whole feature rests on. A script that only
# ever reads stdout must not be able to tell --pretty was even passed.
_out_plain, _err_plain, _rc_plain = _run_agent(_PRETTY_CMDS)
_out_pretty, _err_pretty, _rc_pretty = _run_agent(_PRETTY_CMDS, extra_args=["--pretty"])
check("stdout is byte-for-byte identical whether or not --pretty is passed",
      _rc_plain == 0 and _rc_pretty == 0 and _out_plain == _out_pretty,
      "plain %d bytes, pretty %d bytes" % (len(_out_plain), len(_out_pretty)))
_bad_lines = []
for _ln in _out_pretty.splitlines():
    try:
        json.loads(_ln)
    except ValueError:
        _bad_lines.append(_ln)
check("with --pretty on, every stdout line is still exactly one JSON object",
      not _bad_lines, _bad_lines[:3])
check("--pretty renders to stderr, and only when asked",
      "LEDGER" in _err_pretty and "LEDGER" not in _err_plain, _err_pretty[:200])
check("--pretty never mixes a Python dict repr into the risk rendering",
      "{'" not in _err_pretty, [line for line in _err_pretty.splitlines() if "{'" in line])

# --- the menu ends by starting the game, honours the mortality choice made in it, writes the save
# where ROME_SAVE_DIR says (which beats the config file's own save_dir), and its fogged save is listed
# without leaking the tree's size and resumes.
_menu_dir = tempfile.mkdtemp()
_menu_saves = tempfile.mkdtemp()
_menu_cfg_dir = tempfile.mkdtemp()
_menu_cfg = os.path.join(_menu_cfg_dir, "cfg.json")
json.dump({"save_dir": os.path.join(_menu_cfg_dir, "not_this_one")}, open(_menu_cfg, "w"))
_menu_env = dict(os.environ, ROME_SIM_CONFIG=_menu_cfg, ROME_SAVE_DIR=_menu_saves)
# the menu drops into `play`, so the commands fed are typed words
_menu_input = "1\n1\ny\n\n\ny\n\n\n\nstate\nquit\n"
_pm = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")], input=_menu_input, capture_output=True, text=True,
                     timeout=120, cwd=_menu_dir, env=_menu_env)  # real process: keeps the true entry point covered
check("the menu offers a main menu with New game, Load, and Options",
      all(option in _pm.stdout for option in ("New game", "Load a saved game", "Options")), _pm.stdout[:2000])
check("the menu says it is starting, and names a resumable --session file ending in .json",
      "Starting now" in _pm.stdout and "--session" in _pm.stdout and ".json" in _pm.stdout, _pm.stdout[-500:])
_named = [line.split("--session")[1].strip() for line in _pm.stdout.splitlines() if "--session" in line]
check("ROME_SAVE_DIR decides where the menu's save goes: not beside the cwd, not the config's save_dir",
      bool(_named) and os.path.exists(_named[0]) and os.path.dirname(os.path.abspath(_named[0])) == os.path.abspath(_menu_saves)
      and not [name for name in os.listdir(_menu_dir) if name.endswith(".json")]
      and not os.path.exists(os.path.join(_menu_cfg_dir, "not_this_one")),
      (_named[:1], os.listdir(_menu_saves)))
check("the menu drops straight into a playable session, no extra prompt",
      _pm.returncode == 0 and "YEAR" in _pm.stdout and "WHAT YOU CAN DO NOW" in _pm.stdout, _pm.stdout[-300:])
check("the mortality choice made in the menu reaches the actual game",
      "aged about" in _pm.stdout, _pm.stdout[-300:])
_pl_fogload = cli_in_process.run([], input_text="2\nb\nq\n", cwd=_menu_dir, environment=_menu_env)
check("a fogged save's Load Game entry does not leak how big the tree is",
      "toward Grown and alloy junction transistors" not in _pl_fogload.stdout
      and "technologies built" in _pl_fogload.stdout, _pl_fogload.stdout[-1200:])
_pl_resume = cli_in_process.run([], input_text="2\n1\nstate\nquit\n", cwd=_menu_dir, environment=_menu_env)
check("picking a save from the Load Game list actually resumes it, not a fresh game",
      "Resumed from" in _pl_resume.stdout, _pl_resume.stdout[:600])

# --- the in-game 'options' command: horizon and mortality changes stick across a plain `play --session`
# resume, an explicit --horizon still overrides, and the menu never offers per-game choices mid-game.
_ig_dir = tempfile.mkdtemp()
_ig_session = os.path.join(_ig_dir, "ig.json")
_ig1 = cli_in_process.run(["play", "--civ", "rome_100ad", "--session", _ig_session],
                      input_text="options\n1\n250\nb\noptions\n2\ny\nb\nstate\nquit\n", cwd=_ig_dir)
check("the in-game options command changes the horizon",
      "now ends in 250 AD" in _ig1.stdout, _ig1.stdout[-600:])
check("the in-game options command can turn mortality on mid-game",
      "aged about" in _ig1.stdout, _ig1.stdout[-1200:])
check("the in-game options menu never offers to change civilisation, kit or fog - none of those are honest "
      "to change mid-game",
      not any(option in _ig1.stdout for option in
              ("change the civilisation", "change the kit", "change the starting", "turn fog")),
      [line for line in _ig1.stdout.splitlines() if "fog" in line.lower()])
_ig2 = cli_in_process.run(["play", "--session", _ig_session],
                      input_text="state\nquit\n", cwd=_ig_dir)
check("...and a later plain `play --session` resume - no flag repeated - still honours the horizon and "
      "the mortality",
      "horizon at 250" in _ig2.stdout and "aged about" in _ig2.stdout, _ig2.stdout[-1500:])
_ig3 = cli_in_process.run(["play", "--session", _ig_session, "--horizon", "9"],
                      input_text="state\nquit\n", cwd=_ig_dir)
check("...while an EXPLICIT --horizon flag still overrides the remembered one",
      ("horizon at %d" % (100 + 9)) in _ig3.stdout, _ig3.stdout[-1500:])
_mv_dir = tempfile.mkdtemp()
_mv_from = os.path.join(_mv_dir, "from.json")
_mv_to = os.path.join(_mv_dir, "to.json")
_mv = cli_in_process.run(["play", "--civ", "rome_100ad", "--session", _mv_from],
                     input_text="options\n1\n300\nb\noptions\n3\n%s\nb\nquit\n" % _mv_to, cwd=_mv_dir)
check("moving a save from the in-game options command relocates the file and its remembered horizon",
      os.path.exists(_mv_to) and not os.path.exists(_mv_from) and os.path.exists(_mv_to + ".meta.json"),
      (os.listdir(_mv_dir), _mv.stdout[-400:]))

# THE PRINCIPLE: Options is for the APPLICATION, not for any one game. The
# main-menu Options screen holds save location, display width, rows per
# table, and whether the welcome/tutorial text prints - never per-game
# choices such as civilisation, starting kit, fog, mortality or horizon, by
# the owner's own words: "change where saves are, change language, change
# window size, etc? Not about each save, like fog or mortality?" Those five
# per-game defaults live in "whatever the New Game wizard was told last
# time", written back silently the moment a game actually starts (cli.py's
# _new_game), with no settings screen of their own; horizon and mortality
# stay mid-game-changeable through the in-game 'options' command.
# =============================================================================

_appopt_dir = tempfile.mkdtemp()
_appopt_cfg = os.path.join(_appopt_dir, "cfg.json")
_appopt_env = dict(os.environ, ROME_SIM_CONFIG=_appopt_cfg)
_appopt_env.pop("ROME_SAVE_DIR", None)
_appopt = cli_in_process.run([],
                         input_text="3\nb\nq\n", cwd=_appopt_dir, environment=_appopt_env)
check("...and no longer offers the per-game defaults that used to live here - "
      "civilisation, starting kit, fog, and mortality are a playthrough's own "
      "business, decided when that game starts, not a standing preference",
      not any(option in _appopt.stdout for option in
              ("default civilisation", "default starting kit",
               "default fog of war", "default mortality",
               "default horizon")),
      _appopt.stdout[-1200:])

from sim.engine import settings as _SETTINGS
from sim.ui import cli as _CLI
from sim.ui import protocol as _protocol
_narrow_lines = _CLI._wrap("word " * 40, width=30, indent="   ").splitlines()
_wide_lines = _CLI._wrap("word " * 40, width=150, indent="   ").splitlines()
check("...and, directly: cli._wrap actually uses the width it is given "
      "(narrower wraps the same text into visibly more lines than wider)",
      len(_narrow_lines) > len(_wide_lines) and len(_wide_lines) >= 1,
      (len(_narrow_lines), len(_wide_lines)))
check("...and _apply_display_prefs is what carries an Options override into "
      "both cli._wrap's own default and protocol.DISPLAY_WIDTH - the one "
      "place every renderer reads it from, per protocol.py's own comment",
      (lambda: (_CLI._apply_display_prefs({"display_width": 222}),
               _CLI._DISPLAY_WIDTH == 222 and _protocol.DISPLAY_WIDTH == 222
               )[1])(),
      (_CLI._DISPLAY_WIDTH, _protocol.DISPLAY_WIDTH))
# Reset the module globals _apply_display_prefs just changed, so no later
# check in this file (many of which render through the same shared protocol
# module, in-process) is silently run at width 222 instead of the default.
_CLI._apply_display_prefs(dict(_SETTINGS.CONFIG_DEFAULTS))

# --- rows per table and the welcome text are preferences: with a config that sets rows_per_page and turns
# the welcome off, a new game pages `available` at that many rows and prints no tutorial.
_wt_off_dir = tempfile.mkdtemp()
_wt_off_cfg = os.path.join(_wt_off_dir, "cfg.json")
json.dump({"show_welcome": False, "rows_per_page": 4}, open(_wt_off_cfg, "w"))
_wt_off_env = dict(os.environ, ROME_SIM_CONFIG=_wt_off_cfg, ROME_SAVE_DIR=tempfile.mkdtemp())
_wt_off = cli_in_process.run(["play", "--civ", "rome_100ad", "--session",
                          os.path.join(_wt_off_dir, "s.json")],
                         input_text="available find a\nquit\n",
                         environment=_wt_off_env)
check("a 'rows per table' preference of 4 pages a filtered `available` list at 4 rows, not the old bare 30",
      "1-4 matching" in _wt_off.stdout, _wt_off.stdout[:1500])
check("turning the welcome off from Options suppresses it, and the session still starts and is playable",
      "five to start with" not in _wt_off.stdout and "You arrive in" not in _wt_off.stdout
      and _wt_off.returncode == 0 and "Saved to" in _wt_off.stdout, _wt_off.stdout[:800])

# --- BREAK: the merchant kit is quoted at 4,000 den, Han's price_index is
# 0.750, and the first playable screen said "You arrive in 100 AD with 3000
# cash" with no word anywhere connecting the two numbers. A blind Han
# playthrough picked the kit because it was the recommended middle income
# and then reported the 1,000-den gap as unexplained, twice, as both a
# balance worry and a trust issue. The arithmetic was always right; only
# the silence was a bug.
import re as _re_mk
_mk_dir = tempfile.mkdtemp()
_mk_env = dict(os.environ, ROME_SIM_CONFIG=os.path.join(_mk_dir, "nope.json"),
               ROME_SAVE_DIR=tempfile.mkdtemp())
_mk_play = cli_in_process.run(["play", "--civ", "han_china_100ad", "--kit", "merchant",
                           "--session", os.path.join(_mk_dir, "s.json")],
                          input_text="quit\n", environment=_mk_env)
# Kits are stated in labourer-years, so the kit's size and the cash arrived with (in the civ's own
# coin) must be tied together on the same screen.
_mk_arrived = _re_mk.search(r"arrive in \d+ AD with (\d+)", _mk_play.stdout)
_mk_kit_cash = _re_mk.search(r"which here is (\d+)", _mk_play.stdout)
check("a kit stated in labourer-years and the cash it is worth in the civ's own coin appear together "
      "on the first screen",
      "labourer-years of wages" in _mk_play.stdout
      and _mk_arrived is not None and _mk_kit_cash is not None
      and _mk_arrived.group(1) == _mk_kit_cash.group(1),
      _mk_play.stdout[:1200])
check("with no preference ever set, the welcome/tutorial text still prints on a new game",
      "five to start with" in _mk_play.stdout, _mk_play.stdout[:800])

# --- none of this reaches `agent`: its JSON protocol, and the --pretty
# rendering alongside it, is a stable machine interface that must not vary
# with a human's own saved terminal preferences.
_agentpref_cfg = os.path.join(tempfile.mkdtemp(), "cfg.json")
json.dump({"display_width": 200, "rows_per_page": 2}, open(_agentpref_cfg, "w"))
_agentpref_env = dict(os.environ, ROME_SIM_CONFIG=_agentpref_cfg)
_ap = cli_in_process.run(["agent",
                      "--civ", "rome_100ad", "--pretty"],
                     input_text=json.dumps({"cmd": "available", "find": "a"}) + "\n"
                           + json.dumps({"cmd": "quit"}) + "\n",
                     environment=_agentpref_env)
check("a saved display-width/rows-per-page preference never reaches `agent` "
      "- its --pretty rendering still pages at the old default of 30, "
      "regardless of what a human's own config file says",
      "1-30 matching" in _ap.stderr and "1-2 matching" not in _ap.stderr,
      _ap.stderr[:1200])

# --- the New Game wizard remembers its own last answers as next time's
# defaults, with no settings screen of its own - see settings.py's module
# docstring. Play once with non-default choices; a LATER invocation offers
# those same choices as the default, and accepting every default (blank)
# actually starts a game with them.
_rem_dir = tempfile.mkdtemp()
_rem_cfg = os.path.join(_rem_dir, "cfg.json")
_rem_saves = tempfile.mkdtemp()
_rem_env = dict(os.environ, ROME_SIM_CONFIG=_rem_cfg, ROME_SAVE_DIR=_rem_saves)
# civ 1 (han_china_100ad, not the hardcoded default_civ rome_100ad), fog OFF,
# kit 'merchant' (not the hardcoded default_kit poor_scholar), mortality ON,
# goal left at its default (the blank answer), horizon 321 - deliberately not
# what CONFIG_DEFAULTS starts with.
# TWO NEW WIZARD QUESTIONS LANDED AT ONCE, in different branches: goal
# selection (seventeen goals now, blank takes the default) and the horizon as a
# named-mode menu with "an exact number of years" as one more choice on it
# rather than the only one. 321 matches none of the four named presets, so it
# goes through that fifth option, exactly as a player asking for a number that
# is not named would. Both answers have to be in the script or the wizard
# consumes the horizon as the goal.
_rem1 = cli_in_process.run([],
                       input_text="1\n1\nn\n\nmerchant\ny\n\n5\n321\n\nquit\n", environment=_rem_env)
_rem_cfg_read = json.load(open(_rem_cfg)) if os.path.exists(_rem_cfg) else {}
check("finishing the New Game wizard remembers every answer as next time's "
      "default, with no Options screen involved",
      _rem_cfg_read.get("default_civ") == "han_china_100ad"
      and _rem_cfg_read.get("default_kit") == "merchant"
      and _rem_cfg_read.get("default_fog") is False
      and _rem_cfg_read.get("default_mortal") is True
      and _rem_cfg_read.get("default_horizon") == 321,
      _rem_cfg_read)
_rem2 = cli_in_process.run([],
                       input_text="1\nb\nq\n", environment=_rem_env)
check("...and the civilisation picker offers that remembered choice as its "
      "default the next time the wizard is opened",
      "default 1" in _rem2.stdout, _rem2.stdout[-800:])
_rem3 = cli_in_process.run([],
                       input_text="1\n\n\n\n\n\n\n\n\nstate\nquit\n", environment=_rem_env)
check("...and accepting every default (blank through all six questions) "
      "actually starts the remembered civilisation, not rome_100ad",
      "LATER HAN EMPIRE" in _rem3.stdout.upper(), _rem3.stdout[:2000])
# NOT A BARE 4,000: Han's own price index (0.75x Rome, printed on the WHERE
# AND WHEN screen) scales the merchant kit's nominal capital, so the honest
# check is "more than the poor_scholar default (400), a lot more" rather
# than the kit's own unscaled number.
import re as _re_rem
_rem3_capital = _re_rem.search(r"You arrive in \d+ AD with ([\d,]+)", _rem3.stdout)
check("...and the remembered kit (merchant, not poor_scholar) - far more "
      "starting capital than poor_scholar's 400, scaled by Han's own price "
      "index rather than a bare copy of the kit's nominal den figure",
      _rem3_capital and int(_rem3_capital.group(1).replace(",", "")) > 1000,
      _rem3.stdout[:2000])
check("...the remembered mortality (on)",
      "aged about" in _rem3.stdout, _rem3.stdout[-900:])
check("...and the remembered horizon (321 years)",
      "421" in _rem3.stdout, _rem3.stdout[-900:])

# Money is counted in the money of the place, and in ONE name for it. A break
# tester read "needs about 1959 pence, you have 612 den" in a single sentence:
# one clause localised from the payload, the next from the renderer.
from sim.engine.data import money_short as _money_short


def _render_in_civ_money(game, *names):
    """The typed screens as a player of this civilisation reads them (the money word is set when a game starts)."""
    from sim.ui import protocol as _protocol
    _protocol.MONEY_SHORT = _money_short(game.civ)
    try:
        return "\n".join(_render_pretty(name, ask_agent(game, cmd=name)) for name in names)
    finally:
        _protocol.MONEY_SHORT = "den"


_england = sim(civ="england_1300")
_cur = _render_in_civ_money(_england, "state", "money")
check("an English game is counted in pence and never in denarii",
      " den " not in _cur and "denarii" not in _cur and "pence" in _cur,
      [line for line in _cur.splitlines() if " den " in line or "denarii" in line][:2])
_han_game = sim(civ="han_china_100ad")
_cur2 = _render_in_civ_money(_han_game, "state")
check("a Han game is counted in cash",
      "cash" in _cur2 and "denarii" not in _cur2,
      [line for line in _cur2.splitlines() if "denarii" in line][:2])

# `ventures` fell through to the generic dump and printed lists of dicts as
# raw Python.
_vr = _render_pretty("ventures", ask_agent(_england, cmd="ventures"))
check("ventures is rendered as a table, not as raw Python",
      "CONCERNS" in _vr and "{'id':" not in _vr and "{\"id\":" not in _vr,
      [line for line in _vr.splitlines() if "{'" in line][:2])

# 3. Ten people bought showed as "ON YOUR STAFF: nobody" and "EMPLOY: 0
#    people" while the prompt said art 7, and IN TRAINING printed the trade as
#    the literal string "None" in fractions.
_hh_game = sim(capital=2.0e6)
ask_agent(_hh_game, cmd="buy", what="slaves", n=5)
_hh = _render_pretty("labour", ask_agent(_hh_game, cmd="labour"))
check("people you own appear in your household, not as nobody",
      "people you own" in _hh, [line for line in _hh.splitlines() if "STAFF" in line][:2])
check("a training row without a trade is not printed as None",
      "None x" not in _hh and "None" not in _hh.split("IN TRAINING")[-1][:200],
      _hh.split("IN TRAINING")[-1][:120])
