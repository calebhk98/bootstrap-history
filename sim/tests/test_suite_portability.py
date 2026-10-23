"""The suite must run from a checkout of any name, in any directory. The run itself from a renamed root is
test_suite_portability_smoke.

WHY THIS FILE EXISTS. For as long as the split suite had existed, it imported
itself as `rome.sim.tests` and put the checkout's PARENT on sys.path, so it
only ran if the checkout was in a directory literally named `rome`. The
repository is called bootstrap-history, so `git clone` followed by the command
its own README gives produced:

    ModuleNotFoundError: No module named 'rome'

before a single check executed. That is the loudest possible version of the
failure. The quiet version did more damage: `harness.ROOT` pointed at the
parent too, so a check that globbed `os.path.join(ROOT, "data", ...)` - the
natural spelling - matched nothing at
all. Nine assertions about the civilization files' event coverage ran zero
times, for as long as they had existed, because iterating an empty glob does
not fail. It says nothing, and silence reads exactly like success.

Both failures came from the same root: a path that depended on something
outside the repository. The checks below are structural rather than
behavioural, and they are cheap, because the thing they protect is the ability
to run every other check in this package at all.
"""
QUICK_TOPIC = True

import ast
import os
import re

from .harness import *
from .harness import ROOT, HERE, _LOADTEST_DIR, _PLAY_DIR
from .__main__ import TOPICS


# --- ROOT means the repository, not something near it. Every relative path in
# this package is joined onto ROOT, so if ROOT drifts one level the joins do
# not error, they simply address nothing.
check("harness.ROOT is the repository root, so os.path.join(ROOT, 'data') "
      "addresses this checkout's own data",
      all(os.path.isdir(os.path.join(ROOT, directory))
          for directory in ("data", "sim", "docs", "playtest")),
      ROOT)

check("...and it is THIS checkout, the one the harness itself was imported "
      "from, not another copy that happens to be nearby",
      os.path.abspath(os.path.join(ROOT, "sim")) == os.path.abspath(HERE),
      (ROOT, HERE))

check("the civilization glob that silently matched nothing now matches every "
      "civilization file",
      len([filename for filename
           in os.listdir(os.path.join(ROOT, "data", "civilizations"))
           if filename.endswith(".json") and not filename.startswith("_")]) >= 5,
      sorted(os.listdir(os.path.join(ROOT, "data", "civilizations"))))


# --- Scratch belongs inside the checkout. When ROOT was the parent, a test run
# wrote _loadtest_tmp and _playtest_tmp into whatever directory the checkout
# happened to sit in - someone's home directory, a CI workspace root - where no
# .gitignore covered them and nobody thought to look.
for _scratch in (_LOADTEST_DIR, _PLAY_DIR):
    _abs = os.path.abspath(os.path.join(ROOT, _scratch))
    check("scratch directory %s is created inside the checkout, not beside it"
          % _scratch,
          _abs.startswith(os.path.abspath(ROOT) + os.sep), _abs)


# --- No source file may name the old directory. This is the check that stops
# the bug coming back one call site at a time: a single `os.path.join(ROOT,
# "rome", ...)` added later would be invisible until it either crashed or,
# worse, quietly addressed nothing.
#
# It matches `rome` used as a PATH COMPONENT or a PACKAGE NAME only. "rome" is
# also a perfectly good civilisation id (`S.load_civ("rome")`) and `_rome` is a
# perfectly good local variable, and neither has anything to do with where
# files live; a check that cannot tell those apart would be turned off within
# the week. Comment lines are skipped because this file and harness.py have
# to quote the old name to explain it.
_PATHY_ROME = re.compile(
    r"""["']rome/                # "rome/sim/..." - a path with the old prefix
      | join\([^)]*["']rome["']\s*[,)]   # os.path.join(ROOT, "rome", ...) - a component
      | ^\s*(?:from|import)\s+rome\b   # the rome.sim.tests package import
    """, re.VERBOSE)

# This file is the one exemption, and it has to be: it contains the pattern
# itself, and the prose explaining what the pattern is for. A detector cannot
# scan its own source.
_SELF = os.path.abspath(__file__)

_offenders = []
for _dirpath, _dirnames, _filenames in os.walk(os.path.join(ROOT, "sim")):
    _dirnames[:] = [directory_name for directory_name in _dirnames
                    if directory_name != "__pycache__"]
    for _fn in _filenames:
        if not _fn.endswith(".py"):
            continue
        _p = os.path.join(_dirpath, _fn)
        if os.path.abspath(_p) == _SELF:
            continue
        with open(_p) as _fh:
            for _i, _line in enumerate(_fh, 1):
                if _line.lstrip().startswith("#"):
                    continue
                if _PATHY_ROME.search(_line):
                    _offenders.append("%s:%d" % (os.path.relpath(_p, ROOT), _i))

check("no source file under sim/ addresses a path through a directory named "
      "'rome' - the suite depends on nothing outside the checkout and nothing "
      "about its name",
      not _offenders, _offenders[:10])


# --- A TOPIC MODULE MUST NOT BE ABLE TO END THE RUN.
#
# Every topic module is imported for its side effects: it runs checks at import
# time. So anything else it does at import time happens to the whole run. One
# of them - test_demographics.py - ended with a copy of the runner's own
# epilogue, including `sys.exit(1 if FAILURES else 0)`, left behind when the
# original flat script was split into this package.
#
# The consequence was not a crash. The run printed a well-formed summary line
# and exited 0, having silently skipped the ten topics registered after
# "demographics" - ninety-three checks, including every complaints_* module and
# all four realism_part modules. A suite that reports success for checks it
# never ran is worse than one that fails, because nothing ever draws attention
# to it. This check exists so that it cannot happen a second time.
_exiters = []
_unparsable = []
_tests_dir = os.path.join(ROOT, "sim", "tests")
for _slug in TOPICS:
    _p = os.path.join(_tests_dir, "test_%s.py" % _slug)
    if not os.path.exists(_p):
        _exiters.append("%s: registered in TOPICS but no such file" % _slug)
        continue
    with open(_p, encoding="utf-8") as _handle:
        _source = _handle.read()
    try:
        _tree = ast.parse(_source, filename=_p)   # one parse serves the exit scan and the compile check
    except SyntaxError as _err:
        _unparsable.append("%s: %s" % (_slug, _err))
        continue
    if "exit" not in _source:
        continue
    for _node in ast.walk(_tree):
        # Module level only: a sys.exit inside a def is never reached by the
        # import, and a topic module has no reason to define one anyway.
        if isinstance(_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(_node, ast.Call):
            _f = _node.func
            _name = (_f.attr if isinstance(_f, ast.Attribute)
                     else getattr(_f, "id", None))
            if _name in ("exit", "_exit"):
                _exiters.append("test_%s.py:%d" % (_slug, _node.lineno))

check("no topic module calls sys.exit at import time - a topic that exits "
      "takes every topic after it in TOPICS with it, and the run still prints "
      "a clean summary on its way out",
      not _exiters, _exiters)

check("every discovered topic compiles - a broken file would crash the run "
      "rather than be reported",
      not _unparsable, _unparsable)

# A file that looks like a test but does not match test_*.py is never run.
_near_misses = sorted(
    filename for filename in os.listdir(_tests_dir)
    if filename.lower().startswith("test")
    and not (filename.startswith("test_") and filename.endswith(".py"))
    and not filename.endswith((".pyc", ".pyo")) and filename != "__pycache__")
check("no file in sim/tests looks like a test but escapes the test_*.py "
      "discovery pattern, and nothing is registered by hand",
      not _near_misses and TOPICS == sorted(TOPICS), _near_misses)
