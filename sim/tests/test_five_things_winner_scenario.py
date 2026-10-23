"""SCENARIO: session commands typed mid-game, the frozen manual checkpoint, and the
Endless difficulty horizon: regressions from a player who won the game. The horizon rule and the `--horizon` default are
in test_endless_horizon_rule."""
from .harness import *  # noqa: F401,F403

from sim.tests import cli_in_process


def _play(arguments, text, environment):
    return cli_in_process.run(arguments, text, environment)


# --- Endless, chosen through the wizard, carries a large finite horizon into
# the save (never None), and `options` shows it as Endless, not a nine-digit year.
_endless_saves = tempfile.mkdtemp()
_endless_env = dict(os.environ, ROME_SAVE_DIR=_endless_saves)
_endless_wizard = _play([], "1\n2\ny\n\n\nn\n\n4\n\nquit\n", _endless_env)
_endless_written = [filename for filename in os.listdir(_endless_saves)
                    if filename.endswith(".json") and not filename.endswith(".meta.json")]
check("choosing Endless carries exactly ENDLESS_HORIZON_YEARS into the save's meta sidecar",
      _endless_written and json.load(open(os.path.join(
          _endless_saves, _endless_written[0] + ".meta.json"))).get("horizon_years") == _CLI.ENDLESS_HORIZON_YEARS,
      (_endless_written, _endless_wizard.stdout[-800:]))
_endless_options = (_play(["play", "--session", os.path.join(_endless_saves, _endless_written[0])],
                          "options\nb\nquit\n", os.environ.copy())
                    if _endless_written else None)
check("...and the in-game 'options' screen reads 'none - Endless' for that horizon",
      _endless_options is not None and "none - Endless" in _endless_options.stdout,
      _endless_options.stdout[-1200:] if _endless_options else None)

# --- Session commands typed mid-game, without backing out through menus.
_session_saves = tempfile.mkdtemp()
_session_path = os.path.join(_session_saves, "rome_100ad.json")
_session_env = dict(os.environ, ROME_SAVE_DIR=_session_saves)
_first = _play(["play", "--civ", "rome_100ad", "--session", _session_path],
               "saves\nsave\nquit\n", _session_env)
check("'saves', typed bare mid-game, lists the save directory with the civilisation "
      "and goal progress, and marks which save is this one",
      "SAVES" in _first.stdout and "Roman Empire" in _first.stdout
      and "toward" in " ".join(_first.stdout.split()) and "<- this game" in _first.stdout,
      _first.stdout[-1500:])
_milestones = [filename for filename in os.listdir(_session_saves)
               if "_saved_" in filename and filename.endswith(".json")
               and not filename.endswith(".meta.json")]
# presentation: the interactive play prompts and screens are text
check("bare 'save' writes a new milestone file distinct from the ongoing session file",
      "saved a copy of" in _first.stdout and len(_milestones) == 1
      and os.path.exists(_session_path), (_first.stdout[-600:], os.listdir(_session_saves)))
_milestone_path = os.path.join(_session_saves, _milestones[0])
_milestone_year = re.search(r"saved a copy of (\d+) AD", _first.stdout)
_milestone_bytes_before = open(_milestone_path, "rb").read()
# A separate save directory, so the fork the resume makes cannot become the
# "most recent save" the picker checks below read.
_resume_env = dict(os.environ, ROME_SAVE_DIR=tempfile.mkdtemp())
_resumed = _play(["play", "--session", _milestone_path], "step\nstate\nquit\n", _resume_env)
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
# presentation: the interactive play prompts and screens are text
check("bare 'load' offers a picker over the save directory, and backing out ('b') changes nothing",
      "LOAD A DIFFERENT SAVE" in _backed_out.stdout and "switched to" not in _backed_out.stdout,
      _backed_out.stdout[-1500:])
# presentation: the interactive play prompts and screens are text
check("'restart' asks for confirmation, and declining leaves the game as it was",
      "Start a different game?" in _backed_out.stdout
      and "MAIN MENU" not in _backed_out.stdout.split("Start a different game?")[-1],
      _backed_out.stdout[-800:])
_picked = _play(["play", "--session", _session_path], "load\n1\nstate\nquit\n", _session_env)
# presentation: the interactive play prompts and screens are text
check("picking an entry in the load picker switches this session to it",
      "switched to" in _picked.stdout and "AD." in _picked.stdout, _picked.stdout[-800:])
