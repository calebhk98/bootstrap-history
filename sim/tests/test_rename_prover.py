"""The rename prover has to be right, or it is worse than having nothing.

`sim/prove_rename_safe.py` is what makes the naming sweep affordable. There are
4,972 occurrences of two-character identifiers in this repository and the usual
way to show a refactor was safe - `perf_fingerprint.py` before and after -
cannot be used for them, because it does not currently reproduce its own
recording and, even when it does, it is nine sampled runs rather than a proof.

The prover's claim is stronger than sampling: a local variable's name is not in
the bytecode. CPython addresses locals by slot index (`LOAD_FAST 3`), keeping
the names in a separate `co_varnames` table for tracebacks. So renaming a local
leaves `co_code` byte-identical, while touching an attribute or a global
changes `co_names` and touching a literal changes `co_consts`.

That claim is only worth anything if the tool actually implements it. A
verification tool nobody verified is a rubber stamp, and a rubber stamp on
4,972 edits is how a subtle behaviour change gets waved through. These checks
hand it one known-good and seven known-bad edits and require it to sort them
correctly - if a future change to the prover makes it more permissive, this
fails here rather than silently approving a real change to the simulation.
"""
from .harness import *

import prove_rename_safe as PROVER


_BEFORE = '''
LIMIT = 3
def total(items):
    t = 0.0
    for k in items:
        t += items[k] * LIMIT
    return t

class Thing:
    def go(self, s):
        n = [x * 2 for x in s.values]
        return sum(n)
'''


def _accepts(after):
    return not PROVER.compare(_BEFORE, after, "prover_selftest.py")


# --- WHAT IT MUST ACCEPT. These are the whole point: a rename that only moves
# local names has to come back clean, or the sweep cannot use the tool.
check("the prover accepts a pure local rename",
      _accepts('''
LIMIT = 3
def total(items):
    running_total = 0.0
    for key in items:
        running_total += items[key] * LIMIT
    return running_total

class Thing:
    def go(self, s):
        n = [x * 2 for x in s.values]
        return sum(n)
'''), "")

check("...and a comprehension target, which is its own scope",
      _accepts(_BEFORE.replace("x * 2 for x in", "value * 2 for value in")), "")


# --- WHAT IT MUST REFUSE. Each of these is a real change to what the program
# does, wearing the clothes of a rename. The bytecode comparison catches them
# for a different reason each time, which is why they are listed separately.
check("the prover refuses an ATTRIBUTE rename - that is in co_names, and any "
      "other object with the old attribute breaks",
      not _accepts(_BEFORE.replace("s.values", "s.items_list")), "")

check("...refuses a GLOBAL rename, also co_names",
      not _accepts(_BEFORE.replace("LIMIT", "MAX_LIMIT")), "")

check("...refuses a changed literal, which lives in co_consts",
      not _accepts(_BEFORE.replace("x * 2", "x * 3")), "")

check("...refuses changed logic, the case that matters most: += to -= leaves "
      "every name alone and is not a rename at all",
      not _accepts(_BEFORE.replace("t += items[k]", "t -= items[k]")), "")

check("...refuses an edited docstring, because a docstring is co_consts[0] - "
      "correct, and the reason prose edits belong in their own commit",
      not _accepts(_BEFORE.replace("def total(items):",
                                   'def total(items):\n    """Sum."""')), "")

check("...refuses a renamed method, which is a change to the interface",
      not _accepts(_BEFORE.replace("def go(", "def run(")), "")


# --- THE HOLE IN THE PROOF, ASSERTED SO IT STAYS KNOWN. A parameter rename
# leaves the DEFINING function's bytecode untouched, so the proof passes, while
# any caller writing f(s=...) breaks. The prover cannot see that, and says so
# rather than pretending. NAMING_PLAN.md found a real instance: _did_you_mean's
# `s=` parameter is passed by keyword at three sites in dispatch.py.
_param_renamed = (_BEFORE.replace("def go(self, s):", "def go(self, source):")
                         .replace("s.values", "source.values"))

check("a parameter rename PASSES the bytecode proof - the hole in it, and the "
      "reason parameters are Tier 2 rather than Tier 1",
      _accepts(_param_renamed), "")

check("...but the prover reports it separately, so the call sites get checked "
      "by hand instead of being silently trusted",
      any("parameter s -> source" in note for note in
          PROVER.renamed_parameters(_BEFORE, _param_renamed, "prover_selftest.py")),
      PROVER.renamed_parameters(_BEFORE, _param_renamed, "prover_selftest.py"))


# --- A malformed input must be reported, not crash the sweep or, worse, come
# back clean because nothing could be compared.
check("a file that does not compile is reported, not silently passed",
      not _accepts("def broken(:\n    pass\n"), "")
