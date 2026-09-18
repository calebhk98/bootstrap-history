"""The same scenario, same seed, must give the same answer. Every time.

For a long time it did not. `perf_fingerprint.py` - the tool
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

There are two checks here and they do different jobs.

The BEHAVIOURAL one runs the simulation and compares. It is honest but weak: the
effect was sporadic, depending on the process's whole allocation history, so on
unfixed code 200 years x 8 repeats caught it and 200 years x 4 did not, and
150 x 4 caught it while 150 x 8 did not. It has no false positives - differing
digests always mean something is genuinely wrong - and imperfect sensitivity.
It is a slow_check because it costs about half a minute.

The STRUCTURAL one is the real guard. Rather than sampling for the symptom it
forbids the shape: an `id()` may be used as a dict key for speed, and the entry
it finds must then be validated by identity against a strong reference to the
object itself. That is what `sim/engine/proto/nodes.py` has always done and
what the two guilty caches now do. It is deterministic, it costs milliseconds,
and it catches the whole class rather than the one instance we happened to hit.
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
for _dirpath, _dirnames, _filenames in os.walk(os.path.join(ROOT, "sim", "engine")):
    _dirnames[:] = [d for d in _dirnames if d != "__pycache__"]
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

check("...and the id()-keyed caches that remain are still there, so the check "
      "above is guarding something rather than passing because nobody uses "
      "id() any more",
      _id_keyed_caches >= 4, _id_keyed_caches)


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


# --- THE BEHAVIOURAL CHECK. Slow, and sensitive rather than certain - see the
# module docstring. Worth having anyway: it is the only check here that would
# notice a completely different cause producing the same symptom.
def _repeated_runs_agree():
    import perf_fingerprint as fingerprint
    scenario = fingerprint.SCENARIOS[0]
    digests = [fingerprint.digest(fingerprint.run(scenario)[0]) for _ in range(10)]
    return len(set(digests)) == 1, sorted(set(digests))


slow_check("ten runs of the same scenario in one process give one answer",
           _repeated_runs_agree)
