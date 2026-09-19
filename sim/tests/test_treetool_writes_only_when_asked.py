"""treetool_writes_only_when_asked: every treetool subcommand reports by
default and writes nothing; only `--write` commits a data file.

WHY THIS IS A TEST AND NOT A COMMENT. Two agents wrote `data/judgement.json`
by accident on this project. The second did it while running `judge` to
compare output during an unrelated task, which is the shape of the problem:
`judge` reads as a question, and nothing in the word says it rewrites a
committed file. Both times the instruction to pass `--dry-run` was already
written down, in CLAUDE.md and in the tool's own help. A flag you have to
know about does not protect the person who does not know.

So the default moved, and this pins it there. The check runs the real
subcommands in a subprocess against a COPY of the repository, so a failure
here cannot itself write to `data/`, which would be an unusually unkind way
for a test about accidental writes to fail.
"""
from .harness import *  # noqa: F401,F403

import shutil as _shutil
import subprocess as _subprocess
import sys as _sys
import tempfile as _tempfile
import os as _os

# A whole-repository copy, because treetool resolves `data/` relative to its
# own file. Copying only `data/` would leave the tool writing into the real
# one. The copy is deleted at the end of the module.
_TREETOOL_SANDBOX = _tempfile.mkdtemp(prefix="_treetool_default_")
for _needed in ("sim", "data"):
    _shutil.copytree(_os.path.join(ROOT, _needed),
                     _os.path.join(_TREETOOL_SANDBOX, _needed),
                     ignore=_shutil.ignore_patterns("__pycache__", "*.pyc"))


def _judgement_bytes():
    with open(_os.path.join(_TREETOOL_SANDBOX, "data", "judgement.json"),
              "rb") as handle:
        return handle.read()


def _run_treetool(*arguments):
    return _subprocess.run(
        [_sys.executable, _os.path.join(_TREETOOL_SANDBOX, "sim", "treetool.py")]
        + list(arguments),
        capture_output=True, text=True, timeout=300)


_before = _judgement_bytes()

# --- the headline: the bare command changes nothing.
_plain = _run_treetool("judge")
check("treetool judge exits cleanly with no flags at all",
      _plain.returncode == 0, _plain.stderr[-300:])
check("treetool judge WITHOUT --write leaves data/judgement.json untouched - "
      "the accident this default exists to prevent, where a command that "
      "reads as a question rewrites a committed file",
      _judgement_bytes() == _before,
      "judgement.json changed on a bare `judge`")
check("...and says so, rather than writing silently and leaving the reader "
      "to check git",
      "--write" in _plain.stdout, _plain.stdout[-300:])

# --- the flag that used to be the safe one is still accepted, because it is
#     written into CLAUDE.md, into this project's standing instructions and
#     into scripts. Every caller passing it was asking for what now happens
#     anyway, so breaking them would punish the people who were being careful.
_explicit = _run_treetool("judge", "--dry-run")
check("--dry-run is still accepted rather than being an unknown-argument "
      "error, so every existing caller that was being careful keeps working",
      _explicit.returncode == 0, _explicit.stderr[-300:])
check("...and is a no-op: it writes nothing, which is what it always meant",
      _judgement_bytes() == _before, "judgement.json changed under --dry-run")

# --- and the escape hatch really is an escape hatch. A default that could
#     not be overridden would be a different bug, and a test that only ever
#     checks the safe path would not notice if --write stopped working.
_written = _run_treetool("judge", "--write")
check("--write DOES write, so the safe default is a default and not a "
      "removal of the feature",
      _written.returncode == 0 and _judgement_bytes() != _before
      or _judgement_bytes() == _before and False,
      "exit %s; changed=%s"
      % (_written.returncode, _judgement_bytes() != _before))

# --- every subcommand, not only the one that bit somebody. Which of the four
#     write is exactly what a first-time reader does not know.
for _subcommand in ("judge", "repair", "apply-caps"):
    _snapshot = _judgement_bytes()
    _result = _run_treetool(_subcommand)
    check("treetool %s without --write reports rather than writing" % _subcommand,
          _result.returncode == 0 and _judgement_bytes() == _snapshot,
          "exit %s, stderr %s" % (_result.returncode, _result.stderr[-200:]))

# --- help must not teach the old flag as the way to be safe.
_help_text = _run_treetool("judge", "--help").stdout
check("--help advertises --write and does NOT advertise --dry-run, so "
      "nobody learns the retired flag as the way to be careful",
      "--write" in _help_text and "--dry-run" not in _help_text,
      _help_text[-300:])

_shutil.rmtree(_TREETOOL_SANDBOX, ignore_errors=True)
