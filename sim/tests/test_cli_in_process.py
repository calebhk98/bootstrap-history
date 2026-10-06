"""The in-process CLI runner prints what a real `simulator.py` subprocess prints."""
import subprocess
import sys

from .harness import *  # noqa: F401,F403
from . import cli_in_process

_SIMULATOR = os.path.join(HERE, "simulator.py")


def _both(arguments, input_text):
    real = subprocess.run([sys.executable, _SIMULATOR] + arguments, input=input_text,
                          capture_output=True, text=True, timeout=300, cwd=ROOT)
    return real, cli_in_process.run(arguments, input_text)


_commands = "\n".join(json.dumps(command) for command in
                      [{"cmd": "state"}, {"cmd": "bogus"}, {"cmd": "step"}, {"cmd": "quit"}]) + "\n"
_real, _local = _both(["agent", "--civ", "rome_100ad"], _commands)
check("agent: in-process stdout is byte-identical to a real subprocess",
      _local.stdout == _real.stdout and _real.stdout.count("\n") == 4,
      (_real.stdout[:300], _local.stdout[:300]))
check("...and so are the exit status and the stderr welcome",
      _local.returncode == _real.returncode == 0 and _local.stderr == _real.stderr,
      (_real.returncode, _local.returncode, _real.stderr[-200:], _local.stderr[-200:]))

_real, _local = _both(["agent", "--no-such-flag"], "")
check("a bad argument exits 2 with argparse's message, in-process as in a subprocess",
      _local.returncode == _real.returncode == 2 and _local.stderr == _real.stderr,
      (_real.returncode, _local.returncode, _real.stderr[-200:], _local.stderr[-200:]))

_cwd_before, _argv_before, _stdout_before = os.getcwd(), list(sys.argv), sys.stdout
cli_in_process.run(["agent"], json.dumps({"cmd": "quit"}) + "\n")
check("the runner restores the working directory, argv and streams",
      (os.getcwd(), sys.argv, sys.stdout) == (_cwd_before, _argv_before, _stdout_before))
