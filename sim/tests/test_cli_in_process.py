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
_real, _local = _both(["agent", "--civ", "norse_900ad"], _commands)
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

# Display preferences a command applies (width, rows per page) must not outlast it.
from sim.ui import cli as _cli_module
from sim.ui import protocol as _protocol_module
_display_before = (_cli_module._DISPLAY_WIDTH, _protocol_module.DISPLAY_WIDTH,
                   _protocol_module.DEFAULT_AVAILABLE_LIMIT)
_display_config = os.path.join(tempfile.mkdtemp(), "config.json")
json.dump({"display_width": 150, "rows_per_page": 7}, open(_display_config, "w"))
cli_in_process.run(["play", "--civ", "rome_100ad", "--session", os.path.join(tempfile.mkdtemp(), "s.json")],
                   "quit\n", dict(os.environ, ROME_SIM_CONFIG=_display_config,
                                  ROME_SAVE_DIR=tempfile.mkdtemp()))
check("the runner restores the display width and rows per page a command applied",
      (_cli_module._DISPLAY_WIDTH, _protocol_module.DISPLAY_WIDTH,
       _protocol_module.DEFAULT_AVAILABLE_LIMIT) == _display_before,
      (_display_before, _cli_module._DISPLAY_WIDTH, _protocol_module.DISPLAY_WIDTH,
       _protocol_module.DEFAULT_AVAILABLE_LIMIT))


# --- No state leaks between in-process calls: the same sequence of calls (two civilisations, a
# save then a load through --session, then the first civilisation again) must print what the same
# calls print as separate processes, and a game repeated later must print what it printed first.
def _json_lines(text):
    return [json.loads(line) for line in text.splitlines() if line.startswith("{")]


_steps = "\n".join(json.dumps(command) for command in
                   [{"cmd": "step", "years": 1}, {"cmd": "state"}, {"cmd": "quit"}]) + "\n"
_resume = "\n".join(json.dumps(command) for command in
                    [{"cmd": "state"}, {"cmd": "step"}, {"cmd": "state"}, {"cmd": "quit"}]) + "\n"


def _sequence(runner):
    """Each call's exit status and stdout, with the session path made the same for every pass."""
    session_path = os.path.join(tempfile.mkdtemp(), "leak_check.json")
    calls = [(["agent", "--civ", "han_china_100ad", "--seed", "3", "--session", session_path], _steps),
             (["agent", "--civ", "norse_900ad", "--seed", "3"], _steps),
             (["agent", "--session", session_path], _resume),
             (["agent", "--civ", "han_china_100ad", "--seed", "3"], _steps)]
    outputs = []
    for arguments, text in calls:
        completed = runner(arguments, text)
        outputs.append((completed.returncode, completed.stdout.replace(session_path, "SESSION")))
    return outputs


def _as_subprocess(arguments, text):
    return subprocess.run([sys.executable, _SIMULATOR] + arguments, input=text,
                          capture_output=True, text=True, timeout=600, cwd=ROOT)


_in_process_outputs = _sequence(cli_in_process.run)
_process_outputs = _sequence(_as_subprocess)
check("a sequence of calls (two civilisations, save then load by --session) prints the same in-process as in separate processes",
      _in_process_outputs == _process_outputs
      and all(code == 0 and output for code, output in _in_process_outputs),
      [(call, a[0] == b[0], next((k for k in range(min(len(a[1]), len(b[1]))) if a[1][k] != b[1][k]), None))
       for call, (a, b) in enumerate(zip(_in_process_outputs, _process_outputs))])
check("...and the first game, run again after the others, prints what it printed the first time",
      _in_process_outputs[0][1] == _in_process_outputs[3][1],
      (_in_process_outputs[0][1][:200], _in_process_outputs[3][1][:200]))
check("...and the resumed game carries on from the saved year, not from the opening",
      len(_json_lines(_in_process_outputs[2][1])) >= 3
      and _json_lines(_in_process_outputs[2][1])[0] != _json_lines(_in_process_outputs[0][1])[0],
      _in_process_outputs[2][1][:200])
