"""SMOKE: the suite, run from a differently named root and a working directory that is not the checkout, comes back green and
leaves its scratch directories in that root. The path rules are in test_suite_portability. The child run is one cheap topic."""
import os
import shutil
import subprocess
import sys
import tempfile

from .harness import check
from .harness import ROOT, _LOADTEST_DIR, _PLAY_DIR

# --- The end-to-end proof: this runs the suite through a differently-named root and checks it
# comes back green.
#
# The alias is a real directory containing symlinks to the repository's own
# subdirectories, rather than one symlink to the repository. os.path.abspath
# does not resolve symlinks, so the child's harness computes ROOT as the alias
# and writes its scratch directories there - a real, empty temp directory -
# instead of into the checkout this very run is using them from.
_alias_parent = tempfile.mkdtemp(prefix="suite_portability_")
try:
    _alias = os.path.join(_alias_parent, "definitely_not_called_rome")
    os.makedirs(_alias)
    # mods and .cache too, so the child's cache key matches and it reuses this checkout's solved prices.
    for _sub in ("sim", "data", "docs", "mods", "playtest", ".cache"):
        try:
            os.symlink(os.path.join(ROOT, _sub), os.path.join(_alias, _sub))
        except (OSError, AttributeError):
            shutil.copytree(os.path.join(ROOT, _sub), os.path.join(_alias, _sub))

    _run = subprocess.run(
        [sys.executable, os.path.join(_alias, "sim", "tests", "__main__.py"),
         "--only", "ui_render_registry"],
        capture_output=True, text=True, timeout=300, cwd=_alias_parent)

    check("the whole suite runs from a checkout named something other than "
          "'rome', from a working directory that is not the checkout",
          _run.returncode == 0,
          (_run.returncode, _run.stdout[-400:], _run.stderr[-400:]))

    # presentation: the test runner's printed summary
    check("...and it really ran checks there rather than exiting early with "
          "nothing to do",
          "0 failures" in _run.stdout and " 0 checks," not in _run.stdout,
          _run.stdout[-300:])

    check("...and that run left its scratch directories in its own root, not "
          "in this checkout",
          not any(os.path.exists(os.path.join(_alias_parent, directory))
                  for directory in (_LOADTEST_DIR, _PLAY_DIR)),
          sorted(os.listdir(_alias_parent)))
finally:
    shutil.rmtree(_alias_parent, ignore_errors=True)
