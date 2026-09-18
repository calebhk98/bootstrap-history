#!/usr/bin/env python3
"""Every bug a playtester found, as a test that fails if it comes back.

Nine of these were found by agents playing the game through the JSON protocol,
and three of those were defects in the fix for the previous one. That pattern is
the reason this file exists: a fix verified once by hand is a fix that silently
rots. Run it with `python3 sim/test_regressions.py`.

This used to be the whole suite: one 13,000+ line flat script, every check
running at import in file order, with no way to run only part of it. It is
now a thin shim over the sim.tests PACKAGE (see sim/tests/ - one
module per subject area, plus a runner), so the suite can be run by topic and
edited by more than one person at once without every change colliding in one
file. This file's own behaviour has not changed: `python3
sim/test_regressions.py` still runs every check, in the same order, with
the same summary line and the same exit code, `--slow` and `--jobs N` still
work - see sim/tests/__main__.py for those and for the new `--only
<topics>` / `--list` selection this split adds.
"""
import os
import sys

# sim/tests is a real package (has __init__.py); sim/ is a plain namespace
# package (PEP 420, no __init__.py needed) - which works as long as the REPO
# ROOT is on sys.path, exactly like every other script in this project adds
# sim/ itself for `import simulator`.
#
# This used to root the import one level higher, at the repository's PARENT,
# and import `rome.sim.tests` - so the suite ran only if the checkout was in
# a directory named `rome`. The repository is called bootstrap-history, so a
# fresh clone died on ModuleNotFoundError before running a single check. The
# suite now depends on nothing outside the checkout and nothing about its
# name; clone it anywhere, call it anything, run it from any directory.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from sim.tests.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
