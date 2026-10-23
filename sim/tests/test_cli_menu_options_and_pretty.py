"""SCENARIO (Complaint 640): for the human front end, each a real run of the CLI: the --pretty rendering, the main menu and New Game
wizard, in-game and application options. Every check here reads text a player reads, so each is presentation; the
rules behind them (the money word, the screens, the display width) are called on built replies in
test_pretty_render_built_replies."""
import re as _re

from .harness import *  # noqa: F401,F403
from sim.tests import cli_in_process


def scenario(name, **claims):
    """One named scenario check: it passes when every claim holds, and names the claims that do not."""
    failed = sorted(label for label, held in claims.items() if not held)
    check(name, not failed, failed)  # presentation: the CLI's printed text


def _run_agent(input_lines, extra_args=(), civ="rome_100ad", cwd=None):
    """Drive the real `agent` subcommand in-process (cli_in_process.py), optionally with
    extra CLI flags (--pretty among them). Returns (stdout, stderr, returncode)."""
    arguments = ["agent", "--civ", civ] + list(extra_args)
    proc = cli_in_process.run(arguments, input_text="\n".join(json.dumps(command) for command in input_lines) + "\n",
                              cwd=(cwd or ROOT))
    return proc.stdout, proc.stderr, proc.returncode


# --- --pretty: a script that only reads stdout must not be able to tell it was passed ---------------------------------
_PRETTY_CMDS = [{"cmd": "state"}, {"cmd": "why", "id": "blast_furnace"}, {"cmd": "money"}, {"cmd": "risk"},
                {"cmd": "quit"}]
_out_plain, _err_plain, _rc_plain = _run_agent(_PRETTY_CMDS)
_out_pretty, _err_pretty, _rc_pretty = _run_agent(_PRETTY_CMDS, extra_args=["--pretty"])
_bad_lines = []
for _line in _out_pretty.splitlines():
    try:
        json.loads(_line)
    except ValueError:
        _bad_lines.append(_line)
scenario("scenario: --pretty leaves stdout byte-for-byte what a plain run prints",
         both_succeed=_rc_plain == 0 and _rc_pretty == 0,
         stdout_identical=_out_plain == _out_pretty,
         every_stdout_line_is_one_json_object=not _bad_lines)

# --- the menu ends by starting the game, honours the mortality choice made in it, writes the save where ROME_SAVE_DIR
# says (which beats the config file's own save_dir), and its fogged save is listed without leaking the tree's size and resumes.
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
_named = [line.split("--session")[1].strip() for line in _pm.stdout.splitlines() if "--session" in line]
_pl_fogload = cli_in_process.run([], input_text="2\nb\nq\n", cwd=_menu_dir, environment=_menu_env)
_pl_resume = cli_in_process.run([], input_text="2\n1\nstate\nquit\n", cwd=_menu_dir, environment=_menu_env)
scenario("scenario: the main menu starts a playable, resumable game and saves it where ROME_SAVE_DIR says",
         offers_new_load_options=all(option in _pm.stdout for option in ("New game", "Load a saved game", "Options")),
         says_it_is_starting_and_names_a_session_file="Starting now" in _pm.stdout and "--session" in _pm.stdout and ".json" in _pm.stdout,
         save_goes_to_save_dir_not_cwd_nor_config=bool(_named) and os.path.exists(_named[0])
         and os.path.dirname(os.path.abspath(_named[0])) == os.path.abspath(_menu_saves)
         and not [name for name in os.listdir(_menu_dir) if name.endswith(".json")]
         and not os.path.exists(os.path.join(_menu_cfg_dir, "not_this_one")),
         drops_straight_into_a_session=_pm.returncode == 0 and "YEAR" in _pm.stdout and "WHAT YOU CAN DO NOW" in _pm.stdout,
         mortality_choice_reaches_the_game="aged about" in _pm.stdout,
         fogged_load_entry_does_not_leak_the_tree_size="toward Grown and alloy junction transistors" not in _pl_fogload.stdout
         and "technologies built" in _pl_fogload.stdout,
         picking_a_save_resumes_it="Resumed from" in _pl_resume.stdout)

# --- the in-game 'options' command: horizon and mortality changes stick across a plain `play --session` resume, an
# explicit --horizon still overrides, the menu never offers per-game choices mid-game, and a save can be moved.
_ig_dir = tempfile.mkdtemp()
_ig_session = os.path.join(_ig_dir, "ig.json")
_ig1 = cli_in_process.run(["play", "--civ", "rome_100ad", "--session", _ig_session],
                          input_text="options\n1\n250\nb\noptions\n2\ny\nb\nstate\nquit\n", cwd=_ig_dir)
_ig2 = cli_in_process.run(["play", "--session", _ig_session], input_text="state\nquit\n", cwd=_ig_dir)
_ig3 = cli_in_process.run(["play", "--session", _ig_session, "--horizon", "9"], input_text="state\nquit\n", cwd=_ig_dir)
_mv_dir = tempfile.mkdtemp()
_mv_from = os.path.join(_mv_dir, "from.json")
_mv_to = os.path.join(_mv_dir, "to.json")
cli_in_process.run(["play", "--civ", "rome_100ad", "--session", _mv_from],
                   input_text="options\n1\n300\nb\noptions\n3\n%s\nb\nquit\n" % _mv_to, cwd=_mv_dir)
scenario("scenario: in-game options change the horizon and mortality, stay across a resume, and a save can be moved",
         changes_the_horizon="now ends in 250 AD" in _ig1.stdout,
         turns_mortality_on="aged about" in _ig1.stdout,
         offers_no_per_game_choices=not any(option in _ig1.stdout for option in
                                            ("change the civilisation", "change the kit", "change the starting", "turn fog")),
         a_plain_resume_keeps_horizon_and_mortality="horizon at 250" in _ig2.stdout and "aged about" in _ig2.stdout,
         an_explicit_horizon_flag_overrides=("horizon at %d" % (100 + 9)) in _ig3.stdout,
         moving_a_save_relocates_it_and_its_horizon=os.path.exists(_mv_to) and not os.path.exists(_mv_from)
         and os.path.exists(_mv_to + ".meta.json"))

# --- Options is for the APPLICATION, not for any one game: never per-game choices such as civilisation, starting kit,
# fog, mortality or horizon. Rows per table and the welcome text are preferences.
_appopt_dir = tempfile.mkdtemp()
_appopt_env = dict(os.environ, ROME_SIM_CONFIG=os.path.join(_appopt_dir, "cfg.json"))
_appopt_env.pop("ROME_SAVE_DIR", None)
_appopt = cli_in_process.run([], input_text="3\nb\nq\n", cwd=_appopt_dir, environment=_appopt_env)
_wt_off_dir = tempfile.mkdtemp()
_wt_off_cfg = os.path.join(_wt_off_dir, "cfg.json")
json.dump({"show_welcome": False, "rows_per_page": 4}, open(_wt_off_cfg, "w"))
_wt_off_env = dict(os.environ, ROME_SIM_CONFIG=_wt_off_cfg, ROME_SAVE_DIR=tempfile.mkdtemp())
_wt_off = cli_in_process.run(["play", "--civ", "rome_100ad", "--session", os.path.join(_wt_off_dir, "s.json")],
                             input_text="available find a\nquit\n", environment=_wt_off_env)
scenario("scenario: application Options hold no per-game defaults, and rows per table and the welcome are preferences",
         no_per_game_defaults=not any(option in _appopt.stdout for option in
                                      ("default civilisation", "default starting kit", "default fog of war",
                                       "default mortality", "default horizon")),
         rows_per_table_of_4_pages_available_at_4="1-4 matching" in _wt_off.stdout,
         welcome_off_suppresses_it_and_the_session_plays="five to start with" not in _wt_off.stdout
         and "You arrive in" not in _wt_off.stdout and _wt_off.returncode == 0 and "Saved to" in _wt_off.stdout)

# --- BREAK: the merchant kit is quoted at 4,000 den, Han's price_index is 0.750, and the first playable screen said
# "You arrive in 100 AD with 3000 cash" with no word connecting the two numbers. Kits are stated in labourer-years, so
# the kit's size and the cash arrived with (in the civ's own coin) must be tied together on the same screen.
_mk_dir = tempfile.mkdtemp()
_mk_env = dict(os.environ, ROME_SIM_CONFIG=os.path.join(_mk_dir, "nope.json"), ROME_SAVE_DIR=tempfile.mkdtemp())
_mk_play = cli_in_process.run(["play", "--civ", "han_china_100ad", "--kit", "merchant",
                               "--session", os.path.join(_mk_dir, "s.json")], input_text="quit\n", environment=_mk_env)
_mk_arrived = _re.search(r"arrive in \d+ AD with (\d+)", _mk_play.stdout)
_mk_kit_cash = _re.search(r"which here is (\d+)", _mk_play.stdout)
scenario("scenario: the first screen ties the kit's size to the cash it is worth, and the welcome prints with no preference set",
         kit_and_cash_appear_together="labourer-years of wages" in _mk_play.stdout and _mk_arrived is not None
         and _mk_kit_cash is not None and _mk_arrived.group(1) == _mk_kit_cash.group(1),
         welcome_prints_by_default="five to start with" in _mk_play.stdout)

# --- none of this reaches `agent`: its JSON protocol, and the --pretty rendering alongside it, is a stable machine
# interface that must not vary with a human's own saved terminal preferences.
_agentpref_cfg = os.path.join(tempfile.mkdtemp(), "cfg.json")
json.dump({"display_width": 200, "rows_per_page": 2}, open(_agentpref_cfg, "w"))
_ap = cli_in_process.run(["agent", "--civ", "rome_100ad", "--pretty"],
                         input_text=json.dumps({"cmd": "available", "find": "a"}) + "\n" + json.dumps({"cmd": "quit"}) + "\n",
                         environment=dict(os.environ, ROME_SIM_CONFIG=_agentpref_cfg))
scenario("scenario: a saved display-width and rows-per-page preference never reaches `agent`",
         pages_at_the_default_of_30="1-30 matching" in _ap.stderr, not_at_the_saved_two="1-2 matching" not in _ap.stderr)

# --- the New Game wizard remembers its own last answers as next time's defaults, with no settings screen of its own.
# Play once with non-default choices; a LATER invocation offers those same choices as the default, and accepting every
# default (blank) starts a game with them. 321 matches none of the named horizon presets, so it goes through the
# "an exact number of years" choice, after the goal question (blank takes the default goal).
_rem_dir = tempfile.mkdtemp()
_rem_cfg = os.path.join(_rem_dir, "cfg.json")
_rem_env = dict(os.environ, ROME_SIM_CONFIG=_rem_cfg, ROME_SAVE_DIR=tempfile.mkdtemp())
cli_in_process.run([], input_text="1\n1\nn\n\nmerchant\ny\n\n5\n321\n\nquit\n", environment=_rem_env)
_rem_cfg_read = json.load(open(_rem_cfg)) if os.path.exists(_rem_cfg) else {}
_rem2 = cli_in_process.run([], input_text="1\nb\nq\n", environment=_rem_env)
_rem3 = cli_in_process.run([], input_text="1\n\n\n\n\n\n\n\n\nstate\nquit\n", environment=_rem_env)
_rem3_capital = _re.search(r"You arrive in \d+ AD with ([\d,]+)", _rem3.stdout)
scenario("scenario: the New Game wizard remembers every answer as next time's default and a blank run starts that game",
         config_holds_every_answer=_rem_cfg_read.get("default_civ") == "han_china_100ad"
         and _rem_cfg_read.get("default_kit") == "merchant" and _rem_cfg_read.get("default_fog") is False
         and _rem_cfg_read.get("default_mortal") is True and _rem_cfg_read.get("default_horizon") == 321,
         picker_offers_the_remembered_civilisation="default 1" in _rem2.stdout,
         blank_starts_the_remembered_civilisation="LATER HAN EMPIRE" in _rem3.stdout.upper(),
         # not a bare 4,000: Han's price index scales the merchant kit, so the honest check is a lot more than poor_scholar's 400
         remembered_kit_is_far_richer_than_poor_scholar=bool(_rem3_capital) and int(_rem3_capital.group(1).replace(",", "")) > 1000,
         remembered_mortality="aged about" in _rem3.stdout,
         remembered_horizon_of_321_years="421" in _rem3.stdout)
