"""Session commands typed mid-game, the frozen manual checkpoint, and the
Endless difficulty horizon: regressions from a player who won the game."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.state_waiting import _agent_end_reason

_SIMULATOR = os.path.join(HERE, "simulator.py")


def _play(arguments, text, environment, timeout=60):
    return subprocess.run([sys.executable, _SIMULATOR] + arguments, input=text,
                          capture_output=True, text=True, timeout=timeout, env=environment)


# --- Endless, chosen through the wizard, carries a large finite horizon into
# the save (never None), and `options` shows it as Endless, not a nine-digit year.
_endless_saves = tempfile.mkdtemp()
_endless_env = dict(os.environ, ROME_SAVE_DIR=_endless_saves)
_endless_wizard = _play([], "1\n2\ny\n\n\nn\n\n4\n\nstep\nquit\n", _endless_env, timeout=120)
_endless_written = [filename for filename in os.listdir(_endless_saves)
                    if filename.endswith(".json") and not filename.endswith(".meta.json")]
check("choosing Endless carries exactly ENDLESS_HORIZON_YEARS into the save's meta sidecar",
      _endless_written and json.load(open(os.path.join(
          _endless_saves, _endless_written[0] + ".meta.json"))).get("horizon_years") == _CLI.ENDLESS_HORIZON_YEARS,
      (_endless_written, _endless_wizard.stdout[-800:]))
# Behaviour, not just the sidecar: a game whose end year comes from that horizon is still
# running 600 years in, where the same game under the standard horizon has ended.
_endless_meta = (json.load(open(os.path.join(_endless_saves, _endless_written[0] + ".meta.json")))
                 if _endless_written else {})
_horizon_game = sim()
_horizon_game.year = _horizon_game.cfg["start_year"] + 600
_horizon_game.end_year = _horizon_game.cfg["start_year"] + _endless_meta.get("horizon_years", 0)
_endless_reason = _agent_end_reason(_horizon_game)
_horizon_game.end_year = _horizon_game.cfg["start_year"] + 500
_standard_reason = _agent_end_reason(_horizon_game)
check("choosing Endless lets a game cross where a 500-year Standard horizon has already ended the run",
      _endless_reason is None and _standard_reason is not None,
      (_endless_meta.get("horizon_years"), _endless_reason, _standard_reason))
_endless_options = (_play(["play", "--session", os.path.join(_endless_saves, _endless_written[0])],
                          "options\nb\nquit\n", os.environ.copy())
                    if _endless_written else None)
check("...and the in-game 'options' screen reads 'none - Endless' for that horizon",
      _endless_options is not None and "none - Endless" in _endless_options.stdout,
      _endless_options.stdout[-1200:] if _endless_options else None)

# The --horizon flag keeps its own default; Endless is reached only through the
# wizard or 'options'. Checked on argparse's parsed value, in-process.
_horizon_seen = {}
def _capture_horizon(which):
    def _handler(args):
        _horizon_seen[which] = getattr(args, "horizon", None)
        return 0
    return _handler
_original_argv = sys.argv
_original_handlers = {name: getattr(_CLI, name) for name in
                      ("cmd_run", "cmd_compare", "cmd_play", "cmd_agent")}
try:
    for _name in _original_handlers:
        setattr(_CLI, _name, _capture_horizon(_name))
    for _command_name in ("run", "compare", "play", "agent"):
        sys.argv = ["simulator.py", _command_name]
        _CLI.main()
finally:
    sys.argv = _original_argv
    for _name, _handler in _original_handlers.items():
        setattr(_CLI, _name, _handler)
check("run/compare/play/agent's --horizon flag still defaults to the standard horizon",
      len(_horizon_seen) == 4 and all(value == 500 for value in _horizon_seen.values()),
      _horizon_seen)

# --- Session commands typed mid-game, without backing out through menus.
_session_saves = tempfile.mkdtemp()
_session_path = os.path.join(_session_saves, "rome_100ad.json")
_session_env = dict(os.environ, ROME_SAVE_DIR=_session_saves)
_first = _play(["play", "--civ", "rome_100ad", "--session", _session_path],
               "step\nsaves\nsave\nquit\n", _session_env)
check("'saves', typed bare mid-game, lists the save directory with the civilisation "
      "and goal progress, and marks which save is this one",
      "SAVES" in _first.stdout and "Roman Empire" in _first.stdout
      and "toward" in " ".join(_first.stdout.split()) and "<- this game" in _first.stdout,
      _first.stdout[-1500:])
_milestones = [filename for filename in os.listdir(_session_saves)
               if "_saved_" in filename and filename.endswith(".json")
               and not filename.endswith(".meta.json")]
check("bare 'save' writes a new milestone file distinct from the ongoing session file",
      "saved a copy of" in _first.stdout and len(_milestones) == 1
      and os.path.exists(_session_path), (_first.stdout[-600:], os.listdir(_session_saves)))
_milestone_path = os.path.join(_session_saves, _milestones[0])
_milestone_year = re.search(r"saved a copy of (\d+) AD", _first.stdout)
_milestone_bytes_before = open(_milestone_path, "rb").read()
# A separate save directory, so the fork the resume makes cannot become the
# "most recent save" the picker checks below read.
_resume_env = dict(os.environ, ROME_SAVE_DIR=tempfile.mkdtemp())
_resumed = _play(["play", "--session", _milestone_path], "step 2\nstate\nquit\n", _resume_env)
check("resuming from the milestone reads back its year and says it is a frozen checkpoint",
      _milestone_year
      and ("Resumed the checkpoint at %s: %s AD." % (_milestone_path, _milestone_year.group(1))) in _resumed.stdout
      and "autosaving to" in _resumed.stdout,
      (_milestone_year, _resumed.stdout[:500]))
check("a manual checkpoint is byte-identical on disk after being resumed and played forward",
      open(_milestone_path, "rb").read() == _milestone_bytes_before, _milestone_path)
_forked = re.search(r"autosaving to (\S+) instead", _resumed.stdout)
check("...and the played years went to a separate file, not the checkpoint or the session file",
      _forked and os.path.exists(_forked.group(1))
      and _forked.group(1) not in (_milestone_path, _session_path),
      (_forked and _forked.group(1), os.listdir(_resume_env["ROME_SAVE_DIR"])))

# Backing out of the load picker changes nothing, and declining a restart leaves the game.
_backed_out = _play(["play", "--civ", "rome_100ad", "--session", _session_path],
                    "load\nb\nrestart\nn\nquit\n", _session_env)
check("bare 'load' offers a picker over the save directory, and backing out ('b') changes nothing",
      "LOAD A DIFFERENT SAVE" in _backed_out.stdout and "switched to" not in _backed_out.stdout,
      _backed_out.stdout[-1500:])
check("'restart' asks for confirmation, and declining leaves the game as it was",
      "Start a different game?" in _backed_out.stdout
      and "MAIN MENU" not in _backed_out.stdout.split("Start a different game?")[-1],
      _backed_out.stdout[-800:])
_picked = _play(["play", "--session", _session_path], "load\n1\nstate\nquit\n", _session_env)
check("picking an entry in the load picker switches this session to it",
      "switched to" in _picked.stdout and "AD." in _picked.stdout, _picked.stdout[-800:])
