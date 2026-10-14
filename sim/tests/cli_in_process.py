"""Run `simulator.py <arguments>` inside the test process instead of a new one.

The real entry point (`sim.ui.cli.main`) parses the same argv and dispatches the same command,
with stdin, stdout, stderr, argv, the environment and the working directory swapped in for the
call and restored after, so a test sees what a subprocess would have printed without paying
for a fresh interpreter, imports and data load. A command that would re-exec the interpreter
(`os.exec*`, used to pin the hash seed) is not run here: the caller falls back to a real
subprocess for it.
"""
import contextlib
import io
import os
import subprocess
import sys
import traceback


class ReExecRequested(Exception):
    """The command asked to replace the process; it has to run as a real subprocess."""


class _ProcessState:
    """The module globals a command writes (display units, step hook, unit labels, pushed-back lines).

    A real process starts with them empty and takes them to its grave; here a call starts with them
    empty and the caller's values come back after it.
    """

    def __init__(self):
        from sim.engine import units
        from sim.ui import cli_interactive, units_text
        from sim.ui.proto import step_progress
        self._dictionaries = [units.PREFERENCES, units.CIV_DEFAULTS, units_text.TEXT_LABELS]
        self._lists = [cli_interactive.LINES_PUSHED_BACK]
        self._units, self._step_progress = units, step_progress
        self._saved_dictionaries = [dict(each) for each in self._dictionaries]
        self._saved_lists = [list(each) for each in self._lists]
        self._saved_override = units._registry_override
        self._saved_hook = step_progress._after_year[0]

    def start_fresh(self):
        for each in self._dictionaries + self._lists:
            each.clear()
        self._units._registry_override = None
        self._step_progress._after_year[0] = None

    def restore(self):
        for each, saved in zip(self._dictionaries, self._saved_dictionaries):
            each.clear()
            each.update(saved)
        for each, saved in zip(self._lists, self._saved_lists):
            each[:] = saved
        self._units._registry_override = self._saved_override
        self._step_progress._after_year[0] = self._saved_hook


@contextlib.contextmanager
def _swapped(argv, input_text, environment, cwd):
    saved_streams = sys.stdin, sys.stdout, sys.stderr
    saved_argv, saved_environment, saved_cwd = sys.argv, dict(os.environ), os.getcwd()
    saved_exec = os.execvpe
    # Display preferences a command applies are module globals; a process would take them to its grave.
    from sim.ui import cli, protocol
    saved_display = (cli._DISPLAY_WIDTH, protocol.DISPLAY_WIDTH, protocol.DEFAULT_AVAILABLE_LIMIT)
    process_state = _ProcessState()

    def refuse_exec(*_arguments, **_keywords):
        raise ReExecRequested()
    try:
        sys.stdin, sys.stdout, sys.stderr = io.StringIO(input_text), io.StringIO(), io.StringIO()
        sys.argv = argv
        if environment is not None:
            os.environ.clear()
            os.environ.update(environment)
        # A child process writing to a pipe has no terminal, so it lays text out at the default size.
        os.environ.setdefault("COLUMNS", "80")
        os.environ.setdefault("LINES", "24")
        os.execvpe = refuse_exec
        os.chdir(cwd)
        process_state.start_fresh()
        yield
    finally:
        process_state.restore()
        cli._DISPLAY_WIDTH, protocol.DISPLAY_WIDTH, protocol.DEFAULT_AVAILABLE_LIMIT = saved_display
        os.execvpe = saved_exec
        os.chdir(saved_cwd)
        os.environ.clear()
        os.environ.update(saved_environment)
        sys.argv = saved_argv
        sys.stdin, sys.stdout, sys.stderr = saved_streams


def run(arguments, input_text="", environment=None, cwd=None):
    """`simulator.py arguments` with `input_text` on stdin, as a CompletedProcess."""
    from sim.ui import cli
    simulator_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "simulator.py")
    argv = [simulator_path] + list(arguments)
    working_directory = cwd or os.path.dirname(os.path.dirname(simulator_path))
    try:
        with _swapped(argv, input_text or "", environment, working_directory):
            try:
                cli.main()      # simulator.py ignores what main() returns, so the exit status is 0
                returncode = 0
            except SystemExit as exit_request:
                code = exit_request.code
                returncode = code if isinstance(code, int) else (0 if code is None else 1)
                if code is not None and not isinstance(code, int):
                    sys.stderr.write("%s\n" % code)
            except ReExecRequested:
                raise
            except Exception:
                sys.stderr.write(traceback.format_exc())
                returncode = 1
            stdout, stderr = sys.stdout.getvalue(), sys.stderr.getvalue()
    except ReExecRequested:
        return subprocess.run([sys.executable] + argv, input=input_text, capture_output=True,
                              text=True, env=environment, cwd=working_directory)
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)
