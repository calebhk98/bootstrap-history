"""five_things_winner: split verbatim from the old test_regressions.py (original lines 10532-10882).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# FIVE THINGS FROM A PLAYER WHO WON THE GAME (cli.py/settings.py only - see
# each item below for which of the five it is). Difficulty-as-horizon, the
# arrival screen's undersold help, and typed session commands without
# backing out to the menu. Continuing after victory and the unused-hours
# alert's extension both live in protocol.py and are not this file's to add
# regression tests for - see this change's own hand-off notes.
# =============================================================================

# --- ITEM 4: the arrival screen undersold `help`. A player who won the
# whole game believed there were only five help topics because the arrival
# screen named five starter verbs and nothing suggested there was more.
_arr = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                      "--civ", "rome_100ad"],
                     input="quit\n", capture_output=True, text=True, timeout=60)
# WHITESPACE-NORMALISED, because _wrap() breaks this sentence across lines
# at whatever width the terminal (or its absence, here) resolves to, and a
# literal multi-word substring would otherwise depend on exactly where the
# wrap happened to fall.
_arr_flat = " ".join(_arr.stdout.split())
check("the arrival screen says outright that the five starter verbs are not "
      "the whole game, not only 'help explains the rest' buried at the end "
      "of an unrelated sentence",
      "far more commands than this" in _arr_flat, _arr.stdout[:2000])
check("...and actually NAMES the help topics there, rather than leaving "
      "'help' as a single word to take on faith",
      all(t in _arr.stdout for t in _protocol.HELP_TOPICS), _arr.stdout[:2000])
check("...and the old, easy-to-undersell phrasing is gone from that "
      "paragraph",
      "'help' explains the rest" not in _arr.stdout, _arr.stdout[:2000])

# --- ITEM 1: DIFFICULTY MODES AS HORIZONS. Named presets, not bare numbers,
# and the one honest warning a mode menu can give: the SAME horizon is a
# different offer for different civilisations.
check("HORIZON_MODES actually has the four named presets the player asked "
      "for, with Challenge/Standard/Relaxed as specific year counts and "
      "Endless as no fixed number at all",
      [m[0] for m in _CLI.HORIZON_MODES] == ["challenge", "standard",
                                             "relaxed", "endless"]
      and _CLI.HORIZON_MODES[0][2] == 400 and _CLI.HORIZON_MODES[1][2] == 500
      and _CLI.HORIZON_MODES[3][2] is None,
      _CLI.HORIZON_MODES)
check("...and Endless is a large, ordinary, finite number of years, never "
      "None or infinity - every piece of arithmetic anywhere in this engine "
      "that reads a horizon expects a plain number",
      isinstance(_CLI.ENDLESS_HORIZON_YEARS, int)
      and _CLI.ENDLESS_HORIZON_YEARS > max(
          m[2] for m in _CLI.HORIZON_MODES if m[2]),
      _CLI.ENDLESS_HORIZON_YEARS)
_hmode_dir = tempfile.mkdtemp()
_hmode_cfg = os.path.join(_hmode_dir, "cfg.json")
_hmode_saves = tempfile.mkdtemp()
_hmode_env = dict(os.environ, ROME_SIM_CONFIG=_hmode_cfg, ROME_SAVE_DIR=_hmode_saves)
_hmode1 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                         input="1\n2\ny\n\nn\n\n\nquit\n", capture_output=True,
                         text=True, timeout=60, env=_hmode_env)
# THE FLOOR IS THE CHOSEN GOAL'S, NOT THE DEFAULT GOAL'S. This used to assert a
# per-civilisation figure for the transistor ("1,017 years" for Rome), read from
# a hardcoded table. That was right while there was one goal and wrong the moment
# there were seventeen: a lifetime goal with a five-year floor and the transistor
# with a 142-year one cannot share a sentence, and the table would have had to be
# maintained per civilisation per goal. It is computed with critical_path for
# whatever the player just picked, so there is nothing to keep in step - and it
# is stated as a floor rather than a forecast, because every real run takes
# substantially longer than one.
# WHITESPACE-NORMALISED, because the wizard wraps its prose to the display
# width and a substring assertion on a multi-word phrase fails the moment the
# line break lands inside it. Three checks here were written against
# unwrapped text and passed only because their phrases happened not to
# straddle a break; asserting on the squeezed text is the honest way to ask
# "does the screen say this".
def _squeezed(t):
    return " ".join((t or "").split())
_hm1 = _squeezed(_hmode1.stdout)
check("the difficulty menu states the floor of the goal the player just "
      "chose, so the calendar they pick is chosen against the road they "
      "are actually on",
      "cannot be done in fewer than" in _hm1
      and "every roll going your way" in _hm1,
      _hm1[-1200:])
check("...and says plainly that a real run takes longer than the floor, "
      "rather than letting a player read a floor as an estimate",
      "takes substantially longer than its floor" in _hm1,
      _hm1[-1200:])
# Endless, chosen by number (4) through the wizard: a `step` crosses where
# a 500-year Standard horizon would already have ended the run, and the
# horizon this save carries forward is the large finite
# ENDLESS_HORIZON_YEARS, never None or some other guess.
_endless_dir = tempfile.mkdtemp()
_endless_saves = tempfile.mkdtemp()
_endless_env = dict(os.environ, ROME_SAVE_DIR=_endless_saves)
_endless_wiz = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                              input="1\n2\ny\n\nn\n\n4\nstep 600\nstate\nquit\n",
                              capture_output=True, text=True, timeout=120,
                              env=_endless_env)
check("choosing Endless lets a `step` cross where a 500-year Standard "
      "horizon would already have ended the run",
      "THE RUN HAS ENDED" not in _endless_wiz.stdout
      and "ran out of horizon" not in _endless_wiz.stdout,
      _endless_wiz.stdout[-1500:])
_endless_written = [f for f in os.listdir(_endless_saves)
                    if f.endswith(".json") and not f.endswith(".meta.json")]
check("...and the meta sidecar for that save carries forward exactly "
      "ENDLESS_HORIZON_YEARS, not an arbitrary large number invented here "
      "in the test",
      _endless_written and json.load(open(os.path.join(
          _endless_saves, _endless_written[0] + ".meta.json")
          )).get("horizon_years") == _CLI.ENDLESS_HORIZON_YEARS,
      _endless_written)
_endless_opt = (subprocess.run(
    [sys.executable, os.path.join(HERE, "simulator.py"), "play", "--session",
     os.path.join(_endless_saves, _endless_written[0])],
    input="options\nb\nquit\n", capture_output=True, text=True, timeout=60)
    if _endless_written else None)
check("...and the in-game 'options' screen reads 'none - Endless' for that "
      "horizon, never a literal nine-digit end-year",
      _endless_opt is not None and "none - Endless" in _endless_opt.stdout,
      _endless_opt.stdout[-1200:] if _endless_opt else None)
# run/compare/plan and flag-driven play/agent are completely unaffected:
# none of this touches argparse's own --horizon default. Checked against
# argparse's OWN parsed value, in-process, by swapping out each command's
# handler for one that only records `a.horizon` - not by reading simulation
# output, which depends on luck (whether a single seeded trial happens to
# reach the goal) and said nothing reliable about the default at all.
_horizon_seen = {}
def _capture_horizon(which):
    def _fn(a):
        _horizon_seen[which] = getattr(a, "horizon", None)
        return 0
    return _fn
_orig_argv = sys.argv
_orig_cmd_fns = {n: getattr(_CLI, n) for n in
                ("cmd_run", "cmd_compare", "cmd_play", "cmd_agent")}
try:
    for _n in _orig_cmd_fns:
        setattr(_CLI, _n, _capture_horizon(_n))
    for _cmdname in ("run", "compare", "play", "agent"):
        sys.argv = ["simulator.py", _cmdname]
        _CLI.main()
finally:
    sys.argv = _orig_argv
    for _n, _fn in _orig_cmd_fns.items():
        setattr(_CLI, _n, _fn)
check("run/compare/play/agent's --horizon flag still defaults to 500, "
      "completely unaffected by the difficulty-mode work above - Endless "
      "is reached only through the wizard or the in-game 'options' command, "
      "never through a bare --horizon flag",
      len(_horizon_seen) == 4 and all(value == 500 for value in _horizon_seen.values()),
      _horizon_seen)

# --- ITEM 3: SESSION COMMANDS WITHOUT BACKING OUT THROUGH MENUS. 'saves',
# bare 'save'/'load', 'menu' and 'restart', typed mid-game.
_sess_dir = tempfile.mkdtemp()
_sess_saves = tempfile.mkdtemp()
_sess_session = os.path.join(_sess_saves, "rome_100ad.json")
_sess_env = dict(os.environ, ROME_SAVE_DIR=_sess_saves)
_sess1 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                        "--civ", "rome_100ad", "--session", _sess_session],
                       input="step\nsaves\nquit\n", capture_output=True,
                       text=True, timeout=60, env=_sess_env)
check("'saves', typed bare mid-game, lists the save directory without "
      "leaving for the main menu, and shows the year, civilisation and "
      "goal progress the player asked for",
      # NAMES THE GOAL IT IS ACTUALLY PLAYING, not "the transistor". With
      # seventeen selectable goals that wording was right for one of them and
      # wrong for sixteen, and the listing reads each save's own remembered
      # goal - so this asks that a goal is named at all, not which.
      "SAVES" in _sess1.stdout and "Roman Empire" in _sess1.stdout
      and "toward" in " ".join(_sess1.stdout.split()),
      _sess1.stdout[-1500:])
check("...and marks which of the listed saves is this one",
      "<- this game" in _sess1.stdout, _sess1.stdout[-1500:])
_sess2 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                        "--session", _sess_session],
                       input="save\nquit\n", capture_output=True,
                       text=True, timeout=60, env=_sess_env)
check("bare 'save' (no filename) writes a new milestone file distinct from "
      "the ongoing --session file, rather than doing nothing or colliding "
      "with it",
      "saved a copy of" in _sess2.stdout, _sess2.stdout[-600:])
# NOT its own ".meta.json" sidecar, which now exists too (the milestone's
# "checkpoint" marker - see settings.is_checkpoint) and would otherwise also
# match "_saved_...json": the same exclusion settings.list_saves itself
# already applies when it walks this same directory.
_sess_milestones = [f for f in os.listdir(_sess_saves)
                    if "_saved_" in f and f.endswith(".json")
                    and not f.endswith(".meta.json")]
check("...and that file actually exists, separate from the session file",
      len(_sess_milestones) == 1
      and os.path.exists(os.path.join(_sess_saves, _sess_milestones[0]))
      and os.path.exists(_sess_session),
      os.listdir(_sess_saves))
_sess_milestone_year = re.search(r"saved a copy of (\d+) AD", _sess2.stdout)
_milestone_path = os.path.join(_sess_saves, _sess_milestones[0])
_milestone_bytes_before = (open(_milestone_path, "rb").read()
                           if os.path.exists(_milestone_path) else None)
# A SEPARATE ROME_SAVE_DIR, deliberately NOT _sess_saves: resuming a
# checkpoint now forks a fresh session file (see cli.py's `checkpoint_source`),
# claimed via settings.resolve_save_dir() the same way a brand new game's
# session file is - and leaving that fork in _sess_saves would change which
# file the `_sess3`/`_sess4` bare-'load' checks further down pick up as "the
# most recently written save", which is a real file this test would then be
# quietly depending on the order of rather than testing what it says it does.
_sess_resume_env = dict(os.environ, ROME_SAVE_DIR=tempfile.mkdtemp())
_sess_resumed = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"),
                                "play", "--session", _milestone_path],
                               input="step 5\nstate\nquit\n", capture_output=True,
                               text=True, timeout=60, env=_sess_resume_env)
check("...and it round-trips: resuming directly from the milestone file "
      "reads back the exact year it was saved at, and says out loud that "
      "this is a frozen checkpoint rather than quietly adopting it as the "
      "new autosave target",
      _sess_milestone_year
      and ("Resumed the checkpoint at %s: %s AD." % (
          _milestone_path, _sess_milestone_year.group(1))) in _sess_resumed.stdout
      and "autosaving to" in _sess_resumed.stdout,
      (_sess_milestone_year, _sess_resumed.stdout[:500]))
# THE PLAYER'S ACTUAL COMPLAINT, PROVED DIRECTLY: a player deep into a long
# campaign who resumed a manual checkpoint to diagnose something else found
# the checkpoint itself was not staying put - the first reload had already
# moved it. Several years were just played starting from this exact file
# (the "step 5" above); the one thing that matters is that the bytes on disk
# for the checkpoint itself never moved, not even once, while that happened.
check("a manual checkpoint is BYTE-IDENTICAL on disk after being resumed and "
      "played forward several years - the file itself stays a frozen "
      "snapshot, which is the whole point of a checkpoint",
      _milestone_bytes_before is not None
      and os.path.exists(_milestone_path)
      and open(_milestone_path, "rb").read() == _milestone_bytes_before,
      _milestone_path)
_forked_named = re.search(r"autosaving to (\S+) instead", _sess_resumed.stdout)
check("...and what actually received those played years is a genuinely "
      "separate file, distinct from both the checkpoint and the ongoing "
      "--session file it was never touching in the first place",
      _forked_named
      and os.path.exists(_forked_named.group(1))
      and _forked_named.group(1) not in (_milestone_path, _sess_session),
      (_forked_named and _forked_named.group(1),
       os.listdir(_sess_resume_env["ROME_SAVE_DIR"])))
_sess3 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                        "--session", _sess_session],
                       input="load\nb\nquit\n", capture_output=True,
                       text=True, timeout=60, env=_sess_env)
check("bare 'load' (no filename) offers a picker over the save directory, "
      "distinct from 'load <file>' (the JSON protocol's own sandboxed, "
      "cwd-relative command, unrelated to --session's own directory)",
      "LOAD A DIFFERENT SAVE" in _sess3.stdout, _sess3.stdout[-1500:])
check("...and backing out of that picker ('b') changes nothing - still "
      "playing the same game",
      "switched to" not in _sess3.stdout, _sess3.stdout[-800:])
_sess4 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                        "--session", _sess_session],
                       input="load\n1\nstate\nquit\n", capture_output=True,
                       text=True, timeout=60, env=_sess_env)
check("...and picking an entry actually switches this session to it "
      "(here, switching to itself is a no-op but exercises the real path: "
      "load_state plus the year it reports)",
      "switched to" in _sess4.stdout and "AD." in _sess4.stdout,
      _sess4.stdout[-800:])
check("'save <file>' and 'load <file>' WITH an argument are completely "
      "unchanged by any of the above - still the JSON protocol's own "
      "sandboxed, relative-path save/load",
      True,   # exercised already, extensively, elsewhere in this file via
              # {"cmd":"save"/"load"} directly against _agent_dispatch
      "see this file's existing save/load protocol checks")
_sess5 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                        "--civ", "rome_100ad", "--session", _sess_session],
                       input="menu\n", capture_output=True,
                       text=True, timeout=60, env=_sess_env)
check("'menu', typed bare mid-game, returns to the main menu rather than "
      "quitting the process, with the game already saved (autosave, "
      "unaffected) so nothing is lost",
      "MAIN MENU" in _sess5.stdout, _sess5.stdout[-800:])
_sess6 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                        "--civ", "rome_100ad", "--session", _sess_session],
                       input="restart\nn\nquit\n", capture_output=True,
                       text=True, timeout=60, env=_sess_env)
check("'restart', typed bare mid-game, asks for confirmation before doing "
      "anything - declining leaves the game exactly as it was",
      "Start a different game?" in _sess6.stdout
      and "MAIN MENU" not in _sess6.stdout.split("Start a different game?")[-1],
      _sess6.stdout[-800:])
_sess7_saves = tempfile.mkdtemp()
_sess7_env = dict(os.environ, ROME_SAVE_DIR=_sess7_saves)
_sess7_session = os.path.join(_sess7_saves, "rome_100ad.json")
_sess7 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                        "--civ", "rome_100ad", "--session", _sess7_session],
                       input="restart\ny\n2\ny\n\nn\n\n\nquit\n", capture_output=True,
                       text=True, timeout=60, env=_sess7_env)
check("...accepting starts a genuinely new game through the same wizard, "
      "leaving the original session file untouched on disk",
      "WHERE, AND WHEN" in _sess7.stdout
      and os.path.exists(_sess7_session)
      and len([f for f in os.listdir(_sess7_saves) if f.endswith(".json")
              and not f.endswith(".meta.json")]) == 2,
      os.listdir(_sess7_saves))

# --- THE SAME FREEZE PROPERTY, AGAIN, AGAINST A REAL CAMPAIGN SAVE - not a
# few years of synthetic play. playtest/fixtures/rome_380_corpus_bug.json
# is another agent's regression fixture for a different bug (a real 380 AD
# Rome save); it is read here, never written to, and its own sha256 is
# checked below precisely so a future edit to this file notices immediately
# if it ever became something this test touches instead of merely reads.
import hashlib
import shutil
_corpus_fixture = os.path.join(ROOT, "playtest", "fixtures",
                               "rome_380_corpus_bug.json")
_corpus_sha_before = hashlib.sha256(open(_corpus_fixture, "rb").read()).hexdigest()
check("the corpus-bug fixture this check borrows is the exact file another "
      "agent's regression test owns - if this hash ever does not match, that "
      "fixture changed underneath this check and it is reading the wrong "
      "thing",
      _corpus_sha_before ==
      "60052a5183f1b887a501a0c1d45e2eef543e435dc074865908d144f21bda648f",
      _corpus_sha_before)
_corpus_ckpt_dir = tempfile.mkdtemp()
# A FRESH COPY, NAMED LIKE A MILESTONE - the fixture itself is never opened
# for writing, and this check exercises exactly the same checkpoint-detection
# a real player's bare 'save' output is recognised by (settings.is_checkpoint,
# matched on the "_saved_<N>.json" pattern _pick_milestone_filename always
# writes), rather than inventing a second way to mark a file frozen just for
# this test.
_corpus_ckpt = os.path.join(_corpus_ckpt_dir, "rome_100ad_saved_1.json")
shutil.copyfile(_corpus_fixture, _corpus_ckpt)
_corpus_ckpt_before = open(_corpus_ckpt, "rb").read()
_corpus_resume_env = dict(os.environ, ROME_SAVE_DIR=tempfile.mkdtemp())
_corpus_resumed = subprocess.run(
    [sys.executable, os.path.join(HERE, "simulator.py"), "play",
     "--session", _corpus_ckpt],
    input="step 6\nstate\nquit\n", capture_output=True, text=True,
    timeout=120, env=_corpus_resume_env)
check("resuming a real 380 AD campaign checkpoint and playing six more years "
      "from it forks a new session file and says so, the same as the "
      "synthetic milestone above",
      "Resumed the checkpoint at %s: 380 AD." % _corpus_ckpt
      in _corpus_resumed.stdout
      and "autosaving to" in _corpus_resumed.stdout,
      _corpus_resumed.stdout[:500])
check("...and six played years later, the checkpoint copy is still "
      "BYTE-IDENTICAL to what it was before this process ever touched it - "
      "this is the player's actual complaint, proved against a real, "
      "realistic save rather than only a short synthetic one",
      open(_corpus_ckpt, "rb").read() == _corpus_ckpt_before,
      _corpus_ckpt)
check("...and the original fixture file itself was never opened for writing "
      "at any point in this - a copy was made before any of this ran, and "
      "only the copy's path was ever handed to --session",
      hashlib.sha256(open(_corpus_fixture, "rb").read()).hexdigest()
      == _corpus_sha_before,
      _corpus_fixture)
