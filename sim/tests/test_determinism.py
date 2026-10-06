"""The same scenario, same seed, must give the same answer. Every time.

For a long time it did not. `sim/tests/fingerprint.py` - the tool
`sim/ARCHITECTURE.md` names as the way to prove a change altered nothing - did
not reproduce its own recording: a pristine checkout recorded and then checked
against itself failed two of nine scenarios, at a different scenario and a
different year each run. The whole story, including the wrong turns, is in
`Complaints/closed/27-nondeterministic-simulation.md`.

The cause was an `id()`-reuse hazard. `id()` is a memory address, and it is
only unique among objects that are alive at the same moment; CPython hands a
freed small object's address to the very next same-sized allocation. Two caches
in `economy.py` keyed on `id(demand)` where `demand` was a Counter rebuilt
every tick, so a later tick's Counter regularly landed where an earlier, dead
one had, `cached[0] == id(demand)` read true for two different ticks, and the
cache replayed a stale answer under a fresh year. That path feeds
`project_cost()`, which is why it surfaced as last-bit float drift in a
project's `ph_left` two centuries later.

The behavioural guard (two runs of one seed in one process agree) lives in
test_run_reproducibility.py. This file holds the structural one: rather than
sampling for the symptom it forbids the shape. An `id()` may be used as a dict
key for speed, and the entry it finds must then be validated by identity
against a strong reference to the object itself. It is deterministic, costs
milliseconds, and catches the whole class rather than the one instance hit.

Guards the id()-reuse hazard behind non-determinism; structural, so it catches the class.
"""
import ast
import os

from .harness import *
from .harness import ROOT


# --- THE STRUCTURAL GUARD.
#
# The rule: `id(x)` may appear only as a dictionary key - `CACHE[id(x)]`,
# `CACHE.get(id(x))`. Anywhere else, and in particular in an `==` comparison or
# stashed in a tuple to be compared later, it is being trusted as an identity
# when it is only an address, and that is the bug.
#
# Using it as a dict key is fine and is why these caches are fast: the lookup
# is on an integer. What makes it SAFE is the entry holding the object too, so
# the hit can be confirmed with `is` and the object cannot be collected while
# the entry that might match it is alive.
def _id_aliases(source):
    """Line numbers where the builtin `id` is used as a value rather than
    called (`key = id`, `map(id, xs)`, `sorted(xs, key=id)`, `{id: x}`), which
    would let an address slip past the call check below."""
    tree = ast.parse(source)
    called = {id(node.func) for node in ast.walk(tree)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    return [node.lineno for node in ast.walk(tree)
            if isinstance(node, ast.Name) and node.id == "id"
            and isinstance(node.ctx, ast.Load) and id(node) not in called]


def _id_call_report(path):
    """(allowed, suspect) line numbers for id() calls in one file."""
    tree = ast.parse(open(path).read())
    allowed_calls = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Call)
                and isinstance(node.slice.func, ast.Name)
                and node.slice.func.id == "id"):
            allowed_calls.add(id(node.slice))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in ("get", "setdefault", "pop")):
            for arg in node.args:
                if (isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name)
                        and arg.func.id == "id"):
                    allowed_calls.add(id(arg))
    allowed, suspect = [], []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "id"):
            (allowed if id(node) in allowed_calls else suspect).append(node.lineno)
    return allowed, suspect


_engine_files = []
from .source_dirs import engine_side_dirs
for _dirpath, _dirnames, _filenames in (_entry for _directory in engine_side_dirs() for _entry in os.walk(_directory)):
    _dirnames[:] = [dirname for dirname in _dirnames if dirname != "__pycache__"]
    for _filename in sorted(_filenames):
        if _filename.endswith(".py"):
            _engine_files.append(os.path.join(_dirpath, _filename))

_suspects = []
_id_keyed_caches = 0
for _path in _engine_files:
    _allowed, _suspect = _id_call_report(_path)
    _id_keyed_caches += len(_allowed)
    for _line in _suspect:
        _suspects.append("%s:%d" % (os.path.relpath(_path, ROOT), _line))

check("no engine code compares or stores a bare id() - an address is not an "
      "identity, and trusting one is what made this simulation "
      "non-deterministic",
      not _suspects, _suspects)

check("the alias check sees `id` passed or stored as a value",
      [len(_id_aliases(src)) for src in
       ("key = id\n", "list(map(id, xs))\n", "sorted(xs, key=id)\n", "ok = id(x)\n")]
      == [1, 1, 1, 0])
_aliases = []
for _path in _engine_files:
    for _line in _id_aliases(open(_path).read()):
        _aliases.append("%s:%d" % (os.path.relpath(_path, ROOT), _line))
check("no engine code passes or stores the builtin `id` as a value, which "
      "would hide an address-as-identity from the call check",
      not _aliases, _aliases)

check("...and the id()-keyed caches that remain are still there, so the check "
      "above is guarding something rather than passing because nobody uses "
      "id() any more",
      _id_keyed_caches >= 2, _id_keyed_caches)


# --- Every id()-keyed cache must keep the object itself, not only its address.
# Checked by reading the source of the enclosing function for an `is`
# comparison: crude, but it fails loudly if someone reintroduces a cache that
# looks up by id() and then trusts the hit.
for _path in _engine_files:
    _allowed, _ = _id_call_report(_path)
    if not _allowed:
        continue
    _source = open(_path).read()
    _rel = os.path.relpath(_path, ROOT)
    check("%s looks up by id() and confirms the hit with `is`, so a recycled "
          "address cannot pass as a match" % _rel,
          " is nodes" in _source or " is demand" in _source
          or "is not None and hit[0] is" in _source
          or "entry[0] is" in _source,
          _rel)
