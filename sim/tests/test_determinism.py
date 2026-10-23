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
QUICK_TOPIC = True

import ast
import os
import re
import unittest

from .source_dirs import engine_side_dirs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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


def _id_call_report_of(source):
    """(allowed, suspect) line numbers for id() calls in one source text."""
    tree = ast.parse(source)
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


def _engine_files():
    files = []
    for directory in engine_side_dirs():
        for dirpath, dirnames, filenames in os.walk(directory):
            dirnames[:] = [dirname for dirname in dirnames if dirname != "__pycache__"]
            for filename in sorted(filenames):
                if filename.endswith(".py"):
                    files.append(os.path.join(dirpath, filename))
    return files


# A file whose text has no bare `id` token cannot hold an `id` name, so only the rest are parsed.
BARE_ID = re.compile(r"(?<![\w.])id\b")


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class IdCallReportTests(unittest.TestCase):
    """The scan, called on snippets built here."""

    def test_an_id_as_a_dict_key_is_allowed(self):
        for source in ("CACHE[id(x)] = 1\n", "CACHE.get(id(x))\n", "CACHE.setdefault(id(x), [])\n", "CACHE.pop(id(x), None)\n"):
            self.assertEqual(_id_call_report_of(source), ([1], []), source)

    def test_an_id_compared_or_stashed_is_suspect(self):
        for source in ("same = id(a) == id(b)\n", "seen = (id(a), 3)\n", "last = id(a)\n"):
            allowed, suspect = _id_call_report_of(source)
            self.assertEqual(allowed, [], source)
            self.assertTrue(suspect, source)

    def test_the_alias_check_sees_id_passed_or_stored_as_a_value(self):
        self.assertEqual([len(_id_aliases(source)) for source in
                          ("key = id\n", "list(map(id, xs))\n", "sorted(xs, key=id)\n", "ok = id(x)\n")], [1, 1, 1, 0])


class EngineIdUseTests(unittest.TestCase):
    """The scan, over every engine-side file."""

    @classmethod
    def setUpClass(cls):
        sources = {path: _read(path) for path in _engine_files()}
        cls.files = [path for path, source in sources.items() if BARE_ID.search(source)]
        cls.sources = sources
        cls.reports = {path: _id_call_report_of(sources[path]) for path in cls.files}

    def test_no_engine_code_compares_or_stores_a_bare_id(self):
        suspects = ["%s:%d" % (os.path.relpath(path, ROOT), line)
                    for path, (_allowed, suspect) in self.reports.items() for line in suspect]
        self.assertEqual(suspects, [])

    def test_no_engine_code_passes_or_stores_the_builtin_id_as_a_value(self):
        aliases = ["%s:%d" % (os.path.relpath(path, ROOT), line)
                   for path in self.files for line in _id_aliases(self.sources[path])]
        self.assertEqual(aliases, [])

    def test_the_id_keyed_caches_that_remain_are_still_there(self):
        # so the checks above guard something rather than pass because nobody uses id() any more
        self.assertGreaterEqual(sum(len(allowed) for allowed, _suspect in self.reports.values()), 2)

    def test_every_id_keyed_lookup_confirms_the_hit_with_is(self):
        # Reads the file for an `is` comparison: crude, but it fails loudly if someone reintroduces a cache that
        # looks up by id() and then trusts the hit.
        for path, (allowed, _suspect) in self.reports.items():
            if not allowed:
                continue
            source = self.sources[path]
            self.assertTrue(" is nodes" in source or " is demand" in source or "is not None and hit[0] is" in source
                            or "entry[0] is" in source, os.path.relpath(path, ROOT))


if __name__ == "__main__":
    unittest.main()
