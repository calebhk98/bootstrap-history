"""`proto()` without the subprocess: the real `agent` entry point, run in this
process with stdin and stdout swapped, for checks about what a command replies
rather than about the command line itself (argument parsing, exit codes)."""
import io, json, sys

from .harness import S


def proto_in_process(lines, civ="rome_100ad", kit=None, fog=False):
    """Same arguments and return value as harness.proto()."""
    argv = ["simulator.py", "agent", "--civ", civ]
    if kit:
        argv += ["--kit", kit]
    if fog:
        argv += ["--fog"]
    saved = sys.argv, sys.stdin, sys.stdout, sys.stderr
    stdout = io.StringIO()
    sys.argv = argv
    sys.stdin = io.StringIO("\n".join(json.dumps(command) for command in lines) + "\n")
    sys.stdout, sys.stderr = stdout, io.StringIO()
    code = 0
    try:
        code = S.main() or 0
    except SystemExit as exit_request:
        code = exit_request.code if isinstance(exit_request.code, int) else 1
    finally:
        sys.argv, sys.stdin, sys.stdout, sys.stderr = saved
    parsed_lines = []
    for line in stdout.getvalue().splitlines():
        try:
            parsed_lines.append(json.loads(line))
        except ValueError:
            pass
    return parsed_lines, stdout.getvalue(), code
