"""static_checks: the undefined-name check that a split cannot survive.

WHY THIS TOPIC EXISTS, and it is one specific failure rather than a wish for
tidier code.

`sim/engine/economy.py` was 6,570 lines and was split into a composition point
over four sub-mixins. Six call sites in the moved code used the bare class
object `EconomyMixin` as a process-wide cache slot:

    cached = getattr(EconomyMixin, "_commod_ledger_cache", None)

That worked for as long as those methods lived in the module that defined the
class. Moved into `economy_market.py`, the name resolves nowhere, and it
cannot be imported back because `economy.py` imports `economy_market.py`.

The important part is what did NOT catch it. `python3 -c "import simulator"`
succeeded. `python3 sim/simulator.py validate` passed. Every module compiled,
`ast.parse` was happy, and the whole engine imported clean. The failure
appeared only when a player sent the first command, as

    {"ok": false, "error": "internal error handling that command:
     NameError: name 'EconomyMixin' is not defined."}

A name in a function body is looked up when the line runs, so no amount of
importing proves anything about it. Reading the file does. That is what this
topic does, and it is why it is worth a dependency the rest of the suite does
not have.

Splitting a module into a composition point over several sub-mixins keeps
producing exactly this shape of bug. This check is cheap and it guards
against it directly.

IF RUFF IS NOT INSTALLED this topic skips rather than fails, and says so.
Requiring a tool nobody has would make a clean checkout look broken, which is
a worse failure than the one being guarded against.

    python3 -m pip install ruff
"""
import os
import subprocess
import sys

from .harness import *  # noqa: F401,F403
from .harness import ROOT, SKIPPED


def _ruff_is_available():
    """True when ruff can be run, either on PATH or as a module."""
    for command in (["ruff", "--version"], [sys.executable, "-m", "ruff", "--version"]):
        try:
            finished = subprocess.run(command, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            continue
        if finished.returncode == 0:
            return command[:-1]
    return None


_RUFF = _ruff_is_available()

# THE SOURCE THAT CAN ACTUALLY BE CHECKED. `sim/tests/` opens its modules with
# `from harness import *`, and a star import makes an undefined name
# undecidable: ruff cannot know whether a bare name came from the harness or
# from nowhere, so it reports neither. Those directories are excluded here for
# that reason rather than because their contents matter less. The engine and
# the world modules carry no star import (the last twenty were removed), so
# F821 over them is exact.
#
# THE TOP-LEVEL `sim/*.py` TOOLS WERE MISSING FROM THIS LIST, and the gap was
# found the hard way. `rope`, the refactoring library the naming sweep uses,
# silently mis-renames a comprehension whose loop variable also appears in the
# yielded expression ahead of the `for`: given
#
#     sorted(name for name in dirnames if name not in excluded)
#
# it rewrites the `for` target and the later uses and leaves the FIRST
# occurrence alone, producing a NameError that `py_compile` and `pylint`
# both pass. Four instances were made during one pass over these files, two
# of them in `sim/code_health.py` and `sim/validate_production.py`, and this
# check could not have caught any of them, because it was not looking here.
# They were found by running pyflakes by hand.
#
# These files carry no star import except `simulator.py`, whose wildcard is a
# deliberate re-export (see ruff.toml's per-file-ignores), so F821 over them
# is as exact as it is over the engine. Listed individually rather than as
# the `sim` directory, which would pull in `sim/tests` and defeat the
# exclusion reasoned about above.
_CHECKED_PATHS = ["sim/engine", "sim/world", "tools"] + sorted(
    os.path.join("sim", entry) for entry in os.listdir(os.path.join(ROOT, "sim"))
    if entry.endswith(".py"))

if _RUFF is None:
    SKIPPED.append("static checks: ruff is not installed "
                   "(python3 -m pip install ruff)")
else:
    _finished = subprocess.run(
        _RUFF + ["check", "--isolated", "--select", "F821", "--output-format", "concise"]
        + [os.path.join(ROOT, path) for path in _CHECKED_PATHS],
        capture_output=True, text=True, timeout=300)

    # ruff exits 1 when it finds something and 0 when it does not. Any other
    # code is ruff itself failing, which is not the same as the code being
    # clean and must not be read as a pass.
    _ran_properly = _finished.returncode in (0, 1)
    check("ruff ran to completion, so a clean result means the code was "
          "checked rather than that the checker fell over",
          _ran_properly,
          "exit %s, stderr: %s" % (_finished.returncode, _finished.stderr[-400:]))

    _undefined = [line for line in _finished.stdout.splitlines() if "F821" in line]
    check("no undefined name anywhere in sim/engine, sim/world, tools or the "
          "top-level sim/ tools - this is the check that `import` and "
          "`validate` cannot make, the one a mixin split breaks by moving a "
          "module-global reference, and the one that catches a refactoring "
          "tool silently half-renaming a comprehension",
          _ran_properly and not _undefined,
          "\n".join(_undefined[:20]) or "clean")
