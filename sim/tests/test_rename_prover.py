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

from sim import prove_rename_safe as PROVER


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


# ============================================================================
# THE FOUR HAZARDS FROM NAMING_PLAN.md A.5. Each one is a rename that reads as
# correct and was refused by an earlier version of this prover purely because
# CPython addresses locals by SLOT INDEX: any change to the SET or ORDER of
# slots changed raw co_code even when nothing real changed. See
# prove_rename_safe.py's module docstring for the mechanism (decode the
# instruction stream, compare it with variable operands blanked, check the
# actual names separately). Each hazard below gets an ACCEPT case (the safe
# rename that used to be wrongly refused) and at least one REFUSE case (a
# near-miss that must still fail, so the fix cannot be "just be more lenient").
# ============================================================================

# --- HAZARD 1: SLOT SPLIT. One name bound twice in one function for two
# unrelated meanings shares a slot (NAMING_PLAN.md's own example: `q` in
# treetool.py's cmd_merge meant a resolved prerequisite id in one half and a
# material quantity in the other). Splitting it into two names is safe
# precisely when the two meanings' values never actually flow into each
# other - checked here by two entirely separate loops over the same input.
_BEFORE_SPLIT = '''
def two_meanings(pairs):
    total = 0
    for key, value in pairs:
        q = key
        total += len(q)
    for key, value in pairs:
        q = value
        total += q
    return total
'''

_AFTER_SPLIT_SAFE = '''
def two_meanings(pairs):
    total = 0
    for key, value in pairs:
        resolved_id = key
        total += len(resolved_id)
    for key, value in pairs:
        material_qty = value
        total += material_qty
    return total
'''

check("HAZARD 1 (slot split): one name used for two disjoint meanings in one "
      "function may split into two, when neither meaning's value ever "
      "reaches the other's use",
      PROVER.compare(_BEFORE_SPLIT, _AFTER_SPLIT_SAFE, "split_ok.py") == [],
      PROVER.compare(_BEFORE_SPLIT, _AFTER_SPLIT_SAFE, "split_ok.py"))

# ADVERSARIAL near-miss: the SAME split shape (one old name -> the same two
# new names, in the same places) but the second loop's read is wired to the
# WRONG new name. A check that only counts how many names a slot split into
# would see this as identical to the safe case above; only tracing the actual
# value flow (reaching definitions) catches it.
_AFTER_SPLIT_UNSAFE = '''
def two_meanings(pairs):
    total = 0
    for key, value in pairs:
        resolved_id = key
        total += len(resolved_id)
    for key, value in pairs:
        material_qty = value
        total += resolved_id
    return total
'''

check("...but the identical split is refused the moment a read is wired to "
      "the OTHER new name - same split shape, a real behaviour change, "
      "caught only by tracing value flow, not by counting new names",
      PROVER.compare(_BEFORE_SPLIT, _AFTER_SPLIT_UNSAFE, "split_bad.py") != [],
      "")

# A parameter's own slot must never be split, even where the reaching-
# definitions check alone would have allowed it: its FIRST value comes from
# the caller, at entry, which is a binding no bytecode analysis inside the
# function can see (that is exactly why a parameter RENAME is Tier 2, not
# Tier 1 - see renamed_parameters below).
_BEFORE_PARAMETER_SPLIT = '''
def cmd_merge(q, other):
    first = q
    q = other
    return first, q
'''
_AFTER_PARAMETER_SPLIT = '''
def cmd_merge(q, other):
    first = q
    quantity = other
    return first, quantity
'''
check("...and a PARAMETER's own slot is refused even when nothing else "
      "would have caught it - its identity is set once, by the caller",
      PROVER.compare(_BEFORE_PARAMETER_SPLIT, _AFTER_PARAMETER_SPLIT,
                     "split_param.py") != [],
      "")

# A slot split inside a try/except is refused outright (not provable by this
# file's control-flow graph - see _build_control_flow), never silently passed.
_BEFORE_SPLIT_TRY = '''
def two_meanings(pairs):
    total = 0
    try:
        for key, value in pairs:
            q = key
            total += len(q)
        for key, value in pairs:
            q = value
            total += q
    except ValueError:
        return -1
    return total
'''
_AFTER_SPLIT_TRY = '''
def two_meanings(pairs):
    total = 0
    try:
        for key, value in pairs:
            resolved_id = key
            total += len(resolved_id)
        for key, value in pairs:
            material_qty = value
            total += material_qty
    except ValueError:
        return -1
    return total
'''
check("...and a split inside a try/except is refused, not silently proven, "
      "because this file's control-flow graph does not model exception edges",
      PROVER.compare(_BEFORE_SPLIT_TRY, _AFTER_SPLIT_TRY, "split_try.py") != [],
      "")


# --- HAZARD 2: CELL-VARIABLE ORDERING. co_cellvars is sorted ALPHABETICALLY,
# not by first appearance, so a captured local's new name can move it to a
# different position in that sort - which used to shift its raw slot index
# even though nothing about the closure changed (NAMING_PLAN.md's own
# example: `k` -> `dict_key` failed, `k` -> `ident` passed, purely because
# `ident` happened to sort where `k` did). `zeta`/`alpha` are picked here so
# renaming `alpha` to something that sorts elsewhere is guaranteed to move
# it in co_cellvars, the same way `dict_key` did for `k`.
_BEFORE_CELL_ORDER = '''
def outer(zeta, alpha, gamma):
    def inner():
        return zeta, alpha, gamma
    return inner
'''
_AFTER_CELL_ORDER = '''
def outer(zeta, dict_key, gamma):
    def inner():
        return zeta, dict_key, gamma
    return inner
'''
check("HAZARD 2 (cellvar ordering): a captured local may be renamed to "
      "something that sorts into a different position among its siblings - "
      "co_cellvars' alphabetical order is resolved by NAME here, never by "
      "raw slot index",
      PROVER.compare(_BEFORE_CELL_ORDER, _AFTER_CELL_ORDER, "cellorder_ok.py") == [],
      PROVER.compare(_BEFORE_CELL_ORDER, _AFTER_CELL_ORDER, "cellorder_ok.py"))

# Near-miss: the outer function's own parameter keeps the old name `alpha`,
# but the closure inner() reads is renamed underneath it - inner() now reads
# an undefined global `dict_key` instead of the captured `alpha`. A real
# change (an ATTRIBUTE/GLOBAL appears where a captured local used to be),
# and it must still be refused.
_AFTER_CELL_ORDER_INCONSISTENT = '''
def outer(zeta, alpha, gamma):
    def inner():
        return zeta, dict_key, gamma
    return inner
'''
check("...but refused the moment the rename is not applied consistently "
      "across the closure - that is a real change (a captured local turned "
      "into an undefined global), not a rename",
      PROVER.compare(_BEFORE_CELL_ORDER, _AFTER_CELL_ORDER_INCONSISTENT,
                     "cellorder_bad.py") != [],
      "")


# --- HAZARD 3: FALSE COMPREHENSION COLLISION. Python names every list
# comprehension in a function `<listcomp>` - a tool that matches nested code
# objects BY NAME rather than by position silently compares only one sibling
# and never looks at the others (NAMING_PLAN.md's own example: labour.py's
# _room_advice has three sibling comprehensions and wanted the same rename in
# all three). Three siblings here, each with its own local loop variable
# meaning the same thing.
_BEFORE_SIBLING_COMPREHENSIONS = '''
def rooms(xs, ys, zs):
    a = [x * 2 for x in xs]
    b = [x + 1 for x in ys]
    c = [x - 1 for x in zs]
    return a, b, c
'''
_AFTER_SIBLING_COMPREHENSIONS_OK = '''
def rooms(xs, ys, zs):
    a = [add * 2 for add in xs]
    b = [add + 1 for add in ys]
    c = [add - 1 for add in zs]
    return a, b, c
'''
check("HAZARD 3 (false comprehension collision): three sibling "
      "comprehensions, all named <listcomp>, can all rename their own loop "
      "variable the same way without colliding - each is matched and "
      "checked by POSITION, not by its (shared, ambiguous) name",
      PROVER.compare(_BEFORE_SIBLING_COMPREHENSIONS,
                     _AFTER_SIBLING_COMPREHENSIONS_OK, "siblings_ok.py") == [],
      PROVER.compare(_BEFORE_SIBLING_COMPREHENSIONS,
                     _AFTER_SIBLING_COMPREHENSIONS_OK, "siblings_ok.py"))

# Near-miss: a real behaviour change hidden in the SECOND of three siblings
# (+2 instead of +1). A name-keyed matcher that only ever looks at "some
# <listcomp>" could report this file clean by comparing the wrong sibling
# (or the same one twice) and never seeing the other two at all.
_AFTER_SIBLING_COMPREHENSIONS_BAD = '''
def rooms(xs, ys, zs):
    a = [x * 2 for x in xs]
    b = [x + 2 for x in ys]
    c = [x - 1 for x in zs]
    return a, b, c
'''
check("...but a real change hidden behind the SECOND sibling is still "
      "caught - proof that all three are actually being compared, not just "
      "whichever one a name lookup happens to find first",
      PROVER.compare(_BEFORE_SIBLING_COMPREHENSIONS,
                     _AFTER_SIBLING_COMPREHENSIONS_BAD, "siblings_bad.py") != [],
      "")


# --- HAZARD 4: NESTED DEF NAME. A nested function's own name is a string
# baked into the ENCLOSING function's co_consts (that nested code object's
# own co_name) - renaming a purely local helper changed that string even
# though nothing reachable from outside the enclosing function moved
# (NAMING_PLAN.md's own example: projects.py's institution_unit_cost wanted
# `f` -> `curve` and it was reverted for exactly this reason).
_BEFORE_NESTED_DEF = '''
def institution_unit_cost(u):
    def f(u):
        return u * 2
    return f(u) + 1
'''
_AFTER_NESTED_DEF_OK = '''
def institution_unit_cost(u):
    def curve(u):
        return u * 2
    return curve(u) + 1
'''
check("HAZARD 4 (nested def name): a purely local helper function, only "
      "ever reachable through a name inside its own enclosing function, may "
      "be renamed - it is not part of any interface, so its co_name is "
      "treated like a local, not like a module-level def or a method",
      PROVER.compare(_BEFORE_NESTED_DEF, _AFTER_NESTED_DEF_OK,
                     "nested_def_ok.py") == [],
      PROVER.compare(_BEFORE_NESTED_DEF, _AFTER_NESTED_DEF_OK, "nested_def_ok.py"))

# Near-miss: the same rename, PLUS a real change to the helper's own body.
# The allowance for a nested def's name must not become an allowance for
# anything else about it.
_AFTER_NESTED_DEF_BAD = '''
def institution_unit_cost(u):
    def curve(u):
        return u * 3
    return curve(u) + 1
'''
check("...but refused the moment the renamed helper's OWN body also "
      "changed - the name may move, the logic may not",
      PROVER.compare(_BEFORE_NESTED_DEF, _AFTER_NESTED_DEF_BAD,
                     "nested_def_bad.py") != [],
      "")

# Near-miss: a MODULE-LEVEL function (not nested inside another function) is
# not covered by hazard 4 at all - its name is an interface, exactly like the
# renamed-method case above, and renaming it must still be refused.
check("...and a MODULE-LEVEL function's name is never eligible for this - "
      "hazard 4 is specifically about a def with no outside interface, "
      "which a top-level function is not",
      not _accepts(_BEFORE.replace("def total(items):", "def add_up(items):")),
      "")
