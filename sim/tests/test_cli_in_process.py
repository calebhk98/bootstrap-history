"""cli_in_process (Complaint 640): the in-process runner gives a command a fresh process's globals and puts the
caller's back after it: working directory, argv, streams, environment, display preferences and the unit tables. The
exit status and streams of a command are what its process would have given. Called on commands that build no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from . import cli_in_process as _runner_module
from .cli_in_process import run as run_command   # only commands that build no game are run here

from sim.engine import units
from sim.ui import cli as _cli_module
from sim.ui import protocol as _protocol_module

# --- exit status and streams
_help = run_command(["--help"])
check("a command that exits cleanly gives status 0 and what it printed on stdout",
      _help.returncode == 0 and _help.stdout != "" and _help.stderr == "", (_help.returncode, _help.stderr[-200:]))
_bad = run_command(["agent", "--no-such-flag"])
check("a bad argument gives status 2 and prints to stderr, not stdout",
      _bad.returncode == 2 and _bad.stderr != "" and _bad.stdout == "", (_bad.returncode, _bad.stderr[-200:]))

# --- restoration after a call
_cwd_before, _argv_before, _streams_before = os.getcwd(), list(sys.argv), (sys.stdin, sys.stdout, sys.stderr)
os.environ["CLI_IN_PROCESS_PROBE"] = "kept"
run_command(["--help"], environment={"ONLY": "this"})
check("the runner restores the working directory, argv and streams",
      (os.getcwd(), sys.argv, (sys.stdin, sys.stdout, sys.stderr)) == (_cwd_before, _argv_before, _streams_before))
check("...and the environment a call replaced", os.environ.get("CLI_IN_PROCESS_PROBE") == "kept"
      and "ONLY" not in os.environ, dict(os.environ))
del os.environ["CLI_IN_PROCESS_PROBE"]

_display_before = (_cli_module._DISPLAY_WIDTH, _protocol_module.DISPLAY_WIDTH, _protocol_module.DEFAULT_AVAILABLE_LIMIT)
with _runner_module._swapped(["simulator.py"], "", None, _cwd_before):
    _cli_module._DISPLAY_WIDTH, _protocol_module.DISPLAY_WIDTH, _protocol_module.DEFAULT_AVAILABLE_LIMIT = 150, 150, 7
check("the runner restores the display width and rows per page a command applied",
      (_cli_module._DISPLAY_WIDTH, _protocol_module.DISPLAY_WIDTH, _protocol_module.DEFAULT_AVAILABLE_LIMIT) == _display_before,
      _display_before)

# --- state a call starts fresh and hands back
units.PREFERENCES["probe_unit"] = "kept"
with _runner_module._swapped(["simulator.py"], "", None, _cwd_before):
    _inside = dict(units.PREFERENCES)
    units.PREFERENCES["probe_unit"] = "written inside"
check("a call starts with empty unit preferences, as a new process does", _inside == {}, _inside)
check("...and the caller's unit preferences come back after it", units.PREFERENCES.get("probe_unit") == "kept",
      units.PREFERENCES)
units.PREFERENCES.pop("probe_unit", None)
