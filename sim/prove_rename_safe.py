#!/usr/bin/env python3
"""Prove a rename changed nothing but names.

    python3 sim/prove_rename_safe.py <git-ref>          every .py file, vs that ref
    python3 sim/prove_rename_safe.py <git-ref> sim/engine/labour.py ...
    python3 sim/prove_rename_safe.py --verbose HEAD

Exit 0 means: for every file compared, the only thing that changed is the
spelling of LOCAL variable names. Not the logic, not an attribute, not a
global, not a constant, not a dict key, not a string. Exit 1 names the file
and what else moved.

WHY THIS EXISTS, AND WHY IT IS BETTER THAN THE FINGERPRINT HERE.

This repository has a great many identifiers two characters or shorter;
`python3 sim/code_health.py --names` and `python3 -m pylint sim/` both count
them, and the figure moves every time a pass like this one runs, so it is
deliberately not quoted here.
Fixing them means touching nearly every file, and the usual way to
show a refactor was safe - run `perf_fingerprint.py` before and after - cannot
be used, for two separate reasons. It does not currently reproduce its own
recording (Complaints/27). And even when it does, it is evidence rather than
proof: it says nine reference runs came out the same, not that no behaviour
anywhere could differ.

For renaming local variables there is something much stronger available, and
it comes free from how CPython compiles.

**A local variable's name is not in the bytecode.** Locals are addressed by
slot index - `LOAD_FAST 3`, not `LOAD_FAST "capital"` - and the names live in
a separate table, `co_varnames`, used for introspection and tracebacks.
Captured locals work the same way one level up: `co_cellvars`/`co_freevars`
hold the names, `LOAD_DEREF 1` holds the slot.

THE CATCH, FOUND OVER THREE NAMING ROUNDS (docs/architecture/NAMING_PLAN.md
A.5): comparing raw `co_code` bytes proves too little, because CPython
addresses locals by SLOT INDEX, and several perfectly
safe renames change the SET or ORDER of slots without changing what the
program does:

  * One name bound twice in one function for two unrelated meanings shares a
    slot. Splitting it into two names adds a slot and shifts every later
    index - real bytes change, nothing real changed.
  * `co_cellvars` is sorted ALPHABETICALLY, not by first appearance. Renaming
    a captured local can move it to a different position in that sort, which
    shifts its index even though nothing about the closure changed.
  * Two comprehensions of the same kind in one function are BOTH named
    `<listcomp>` (Python does not disambiguate them). A tool that matches code
    objects by name silently compares only one of them and misses edits to
    the other entirely - the opposite of proving anything.
  * A nested `def`'s own name is a string baked into the ENCLOSING function's
    `co_consts` (as that nested code object's `co_name`). Renaming a purely
    local helper function changes that string even though nothing reachable
    from outside the enclosing function moved.

So instead of raw bytes, this file DECODES the instruction stream (via
`dis.get_instructions(code, adaptive=False)` - the canonical, non-specialised
form; see `_instructions`) and compares it NAME-AWARE: every
LOAD_FAST/STORE_FAST/DELETE_FAST and LOAD_DEREF/STORE_DEREF/DELETE_DEREF/
LOAD_CLOSURE/LOAD_CLASSDEREF/MAKE_CELL is reduced to its OPCODE only in the
main stream (the slot index is deliberately invisible here - that is exactly
what a rename, a split or a cellvar reorder are free to move), and the actual
variable NAMES (already resolved by `dis` through co_varnames/co_cellvars/
co_freevars, regardless of that table's order) are compared separately, in
order, to confirm they form a rename rather than something else. See
`_check_local_domain`/`_check_free_domain` for exactly what "something else"
means and how much of it this file can and cannot tell apart from a rename.
Nested code objects (functions, lambdas, comprehensions, classes) are matched
up POSITIONALLY rather than by name (`_nested_children`/`_compare_code_pair`),
which is what lets same-named siblings and renamed nested helpers be handled
correctly instead of silently skipped or refused.

Everything else - attributes, globals, literals, operators, call shape,
control flow, docstrings - is still compared with full fidelity (`arg` AND
`argval` together for a generic instruction; the raw, non-code entries of
`co_consts`; `co_names`), so none of that gets any more permissive than the
old byte-for-byte comparison was.

    co_code, name-aware   must be identical apart from which SLOT/NAME
                           a LOAD_FAST/STORE_FAST/.../LOAD_DEREF/... touches
    co_names              must be identical           (attributes, globals, methods)
    co_consts             must be identical           (literals, and nested functions,
                                                         compared recursively)
    local/cell/free names MAY differ, under the rules above

If all of that holds, the two files execute the same instructions against the
same attributes with the same constants, using the same (or, for the four
hazards above, a provably equivalent) set of names for their locals. That is
not a sample of nine runs. It is every possible run.

WHAT IT DOES NOT COVER, and you must read this before trusting it:

  * **Only local and captured-local renames.** Renaming an attribute, a
    parameter that callers pass by keyword, a global, a dict key or a string
    is a real change and this tool will correctly refuse it. That is the
    point - it is the Tier 1 / Tier 2 boundary from
    docs/architecture/NAMING_PLAN.md, enforced mechanically instead of by eye.
  * **Not keyword arguments.** A parameter rename leaves the DEFINING
    function's proof clean, while any caller using `f(s=...)` breaks.
    Parameters are Tier 2 for exactly this reason. `--check-params` reports
    which renamed locals are parameters, so you can check their call sites by
    hand.
  * **Not a MERGE.** Renaming a local ONTO a name that already exists in the
    same scope is the mirror image of the slot-split hazard, and this file
    does not attempt to prove one safe - NAMING_PLAN.md's own advice for that
    case is to grep the function and pick a name that is not already there,
    not to rely on a proof. A merge is always reported as a real difference.
  * **Not a split of a PARAMETER's own slot**, nor a split anywhere inside a
    function that contains a `try`/`except`/`finally`/`with` (CPython's
    zero-cost exception table can move control out of the middle of a block
    with no `JUMP_*` anywhere in sight, and this file's control-flow graph -
    built only from jump instructions, see `_build_control_flow` - does not
    model that; under-counting a path is the DANGEROUS direction for this
    proof, so the safe response is to decline rather than guess). Both are
    reported as real differences requiring a by-hand check, never silently
    accepted.
  * **A captured passthrough variable used ONLY to build a further-nested
    closure, with no local read of its own** (see `_check_free_domain`) is
    the one corner where this file's cellvar-ordering fix can fall back to a
    weaker, count-only check instead of confirming an exact name-for-name
    correspondence. Rare in practice, and never on the accepting side of an
    actual mismatch - see that function's docstring for exactly what it
    still catches.
  * **An opcode this file has never been shown.** `_assert_known_variable_opcodes`
    refuses to run rather than guess if it meets an opcode that looks like it
    touches a variable but is not one this file's tables (themselves read
    from `dis.haslocal`/`dis.hasfree`, so they track this interpreter
    automatically) know about - see that function for why.
  * **Docstrings yes, COMMENTS NO.** A docstring is `co_consts[0]`, so editing
    one fails this check - correct, if occasionally annoying, and the reason
    to keep a rename commit free of prose edits.

    A comment is a different matter and it is this tool's real blind spot.
    Comments are discarded by the compiler and appear nowhere in a code
    object, so a rename that deleted or mangled every comment in a file would
    pass here with a clean bill of health. In this repository that is not a
    small gap: five of eight engine files are majority comment, and CLAUDE.md
    calls them load-bearing, because they are how one agent hands the next the
    reason a thing is the way it is.

    So a proven rename still needs one more check, which is cheap:

        git diff -U0 | grep -E "^[-+]\\s*#"

    Nothing should come back. Do that before believing this tool, not after.
  * **Nothing about whether the new name is any good.** That is a review.

VERIFIED AGAINST CPython 3.11.15. Python 3.13 added "superinstructions" such
as `LOAD_FAST_LOAD_FAST` that pack two variable references into one opcode;
this interpreter has none of them, so this file's handling of that shape has
never actually run. `_assert_known_variable_opcodes` is the safety net for
that gap: it raises rather than silently treating an unrecognised opcode's
operand as an ordinary constant.
"""
import argparse
import collections
import dis
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# --- Opcode classification, read from `dis` itself rather than hand-copied,
# so a future Python version's own additions (say, a new LOAD_FAST_CHECK
# variant) are picked up with no edit here, as long as `dis` still resolves
# it to a single variable name in `argval` - see _assert_known_variable_opcodes
# for what happens when that stops being true.
#
# `haslocal` addresses co_varnames (LOAD_FAST/STORE_FAST/DELETE_FAST on
# 3.11.15). `hasfree` addresses the combined co_cellvars+co_freevars table
# (MAKE_CELL, LOAD_CLOSURE, LOAD_DEREF, STORE_DEREF, DELETE_DEREF,
# LOAD_CLASSDEREF on 3.11.15).
_LOCAL_OPNAMES = frozenset(dis.opname[opcode] for opcode in dis.haslocal)
_FREE_OPNAMES = frozenset(dis.opname[opcode] for opcode in dis.hasfree)

# LOAD_CLOSURE is the one member of _FREE_OPNAMES whose EMISSION ORDER is not
# reliable evidence of correspondence: it builds a child closure's tuple in
# the CHILD's alphabetically-sorted freevar order, so renaming a captured
# local can reorder these instructions relative to each other even though
# nothing about the closure changed. See _check_free_domain.
_ORDER_UNRELIABLE_FREE_OPNAMES = frozenset({"LOAD_CLOSURE"})
_RELIABLE_FREE_OPNAMES = _FREE_OPNAMES - _ORDER_UNRELIABLE_FREE_OPNAMES

# Opcodes that end a basic block for _build_control_flow's purposes: control
# never falls through them to the next instruction (ignoring the exception
# table - see that function's docstring for why this is the safe direction to
# be wrong in, if it is wrong at all).
_TERMINAL_OPNAMES = frozenset({"RETURN_VALUE", "RETURN_CONST", "RAISE_VARARGS", "RERAISE"})
_UNCONDITIONAL_JUMP_OPNAMES = frozenset(
    {"JUMP_FORWARD", "JUMP_BACKWARD", "JUMP_BACKWARD_NO_INTERRUPT"})

# A loud tripwire for _assert_known_variable_opcodes: substrings that show up
# in every variable-touching opcode name this file knows about, on every
# CPython version from 3.8 through 3.13's superinstructions. If an opcode
# carries one of these markers but is not in _LOCAL_OPNAMES/_FREE_OPNAMES,
# this interpreter has an opcode this file has never been shown.
_SUSPECT_VARIABLE_MARKERS = ("FAST", "DEREF", "CLOSURE", "CELL")


def compile_source(source, filename):
    return compile(source, filename, "exec", dont_inherit=True)


def _instructions(code):
    """The canonical instruction stream for one code object.

    `adaptive=False` asks for the instructions as originally compiled, before
    CPython's specialising/adaptive interpreter would have rewritten some of
    them in place (a plain `LOAD_FAST` can become a type-specialised variant
    after running a few times) - a freshly compiled code object never has
    these anyway, but this is passed explicitly so that stays true if it ever
    changes. The default `show_caches=False` hides the CACHE pseudo-slots
    3.11 reserves after some instructions for that same adaptive interpreter
    to fill in later; they carry no information about the source program.
    """
    return list(dis.get_instructions(code, adaptive=False))


def _assert_known_variable_opcodes(code, label):
    """Refuse to proceed if `code` contains an opcode that LOOKS like it
    touches a local or captured variable but is not one this file's tables
    know about on this interpreter.

    Silently falling through to the generic (opname, arg, argval) comparison
    for such an opcode would treat its variable operand like an ordinary
    constant: mostly harmless (a spurious refusal - a real rename would look
    like a "changed constant" and fail this check, which is annoying but
    safe), except that a future opcode whose `argval` HAPPENS to already look
    like a plain name (rather than, say, the two-name tuple a
    LOAD_FAST_LOAD_FAST-style superinstruction would need) could slip through
    that generic path and be silently treated as a correct comparison when it
    is not. This is a loud, explicit check instead of trusting that it can't
    happen: raise, name the opcode and the interpreter version, and say what
    to do, rather than guess.
    """
    for instruction in _instructions(code):
        opname = instruction.opname
        if opname in _LOCAL_OPNAMES or opname in _FREE_OPNAMES:
            continue
        if any(marker in opname for marker in _SUSPECT_VARIABLE_MARKERS):
            raise RuntimeError(
                "%s: opcode %s touches a variable but is not in "
                "dis.haslocal/dis.hasfree on this interpreter (Python %s). "
                "prove_rename_safe.py's variable normalisation was verified "
                "against 3.11.15 and does not know this opcode's shape - "
                "likely a newer superinstruction such as LOAD_FAST_LOAD_FAST "
                "that packs more than one variable reference into one "
                "instruction. Update _LOCAL_OPNAMES/_FREE_OPNAMES's handling "
                "in this file for this Python version before trusting it, "
                "rather than letting the operand be silently compared like "
                "an ordinary constant." % (label, opname, sys.version.split()[0]))


def _consts_without_code(code):
    """co_consts with nested code objects removed - those compare separately.

    This is what still catches an edited or added/removed constant that is
    never actually loaded by a LOAD_CONST at all - most notably a docstring,
    which the compiler stores at co_consts[0] and exposes as `__doc__` on the
    function object WITHOUT ever emitting an instruction to load it. The
    instruction-stream comparison in `_compare_code_pair` would not see a
    docstring edit by itself; this does.
    """
    return tuple(constant for constant in code.co_consts if not hasattr(constant, "co_code"))


def _nested_children(code):
    """Every nested code object directly inside this one's co_consts, in the
    order the compiler placed them there - deliberately NOT by name, because
    Python gives every list comprehension in a function the same name,
    `<listcomp>` (same for `<setcomp>`, `<dictcomp>`, `<genexpr>`), so two
    siblings of the same kind would collide under any name-keyed matching and
    one of them would be silently skipped instead of compared."""
    return [const for const in code.co_consts if hasattr(const, "co_code")]


def _is_fast_scope(code):
    """True for a function, lambda or comprehension/genexpr body - anything
    that addresses its locals by fast-local slot (CO_OPTIMIZED, flag 0x1).
    False for a module or a class body, which use a name-based namespace
    (LOAD_NAME/STORE_NAME/LOAD_ATTR) instead and have no fast locals of
    their own. This is what tells `_compare_code_pair` whether a nested
    code object's own name is reachable from outside (a module-level def or
    a method, found under a module or a class - must match by name) or only
    reachable through a local inside the function that defines it (found
    under a function/lambda/comprehension - free to be renamed, exactly like
    a local, because that is what it is)."""
    return bool(code.co_flags & 0x1)


def _fixed_syntactic_name(name):
    """True for a name Python assigns automatically that no source text can
    spell differently: `<module>`, `<lambda>`, `<listcomp>`, `<setcomp>`,
    `<dictcomp>`, `<genexpr>` and similar. A pair of code objects with one of
    these names must keep it - if it changed, the underlying CONSTRUCT itself
    changed shape (e.g. a list comprehension became a generator expression),
    which is a real difference, not a rename."""
    return name.startswith("<") and name.endswith(">")


def _normalised_instruction(instruction):
    """One instruction, reduced to what a rename is and is not allowed to
    touch.

    - LOAD_FAST/STORE_FAST/DELETE_FAST and LOAD_DEREF/STORE_DEREF/
      DELETE_DEREF/LOAD_CLOSURE/LOAD_CLASSDEREF/MAKE_CELL (found via
      `dis.haslocal`/`dis.hasfree`): the slot is blanked here. Its NAME is
      checked separately, in order, by `_check_local_domain`/
      `_check_free_domain` - never by the numeric slot index, which is
      exactly what a rename, a slot split or a cellvar reorder are all free
      to move.
    - LOAD_CONST of a nested code object: blanked here too, and that code
      object is compared recursively by `_compare_code_pair` instead - two
      compiled code objects are not comparable with `==` in any way that
      would mean "the same program", so nothing meaningful would be checked
      by comparing them directly at this point.
    - everything else: `(opname, arg, argval)` together - full fidelity,
      equivalent to comparing raw bytes for these instructions. This is what
      keeps an attribute rename, a global rename, a changed literal, a
      changed operator or a changed call shape failing exactly as before:
      none of those opcodes are in `dis.haslocal`/`dis.hasfree`, so none of
      them are blanked.
    """
    opname = instruction.opname
    if opname in _LOCAL_OPNAMES or opname in _FREE_OPNAMES:
        return (opname, "<variable>")
    if opname == "LOAD_CONST" and hasattr(instruction.argval, "co_code"):
        return (opname, "<nested code>")
    return (opname, instruction.arg, instruction.argval)


def _normalised_stream(instructions):
    return [_normalised_instruction(instruction) for instruction in instructions]


def _build_control_flow(instructions):
    """A basic-block control-flow graph over an ALREADY-VERIFIED-IDENTICAL
    instruction stream (`_compare_code_pair` only calls this after the two
    normalised streams compared equal), used only to check whether a slot
    split (hazard 1 - one local reused for two meanings) is safe. Blocks are
    keyed by the index, into `instructions`, of their first instruction.
    Returns `(block_of, block_end, successors, block_starts)`.

    This is deliberately biased towards MORE edges rather than fewer. It does
    not know about CPython's zero-cost exception table (`co_exceptiontable`),
    which can transfer control out of the middle of a block on any
    instruction that might raise, with no `JUMP_*` opcode anywhere nearby.
    Missing such an edge would make the reaching-definitions analysis below
    UNDER-count how a value could reach a use, which could wrongly clear a
    split that is only safe on the paths this graph happens to model - the
    dangerous direction for a soundness proof. So `_check_local_domain` only
    ever attempts a split when `co_exceptiontable` is empty for BOTH the old
    and the new code (no `try`/`except`/`finally`/`with` anywhere in the
    function at all), and this graph's remaining looseness - treating
    `FOR_ITER`/`SEND` as always both jumping AND falling through, whether or
    not that particular case can truly do both - only ever adds edges,
    which only ever makes the safety check below MORE conservative, never
    less.
    """
    instruction_count = len(instructions)
    offset_to_index = {instruction.offset: index
                       for index, instruction in enumerate(instructions)}
    is_leader = [False] * instruction_count
    if instruction_count:
        is_leader[0] = True
    for index, instruction in enumerate(instructions):
        is_branch = (instruction.opcode in dis.hasjrel
                    or instruction.opcode in dis.hasjabs)
        if is_branch:
            is_leader[offset_to_index[instruction.argval]] = True
        ends_block = is_branch or instruction.opname in _TERMINAL_OPNAMES
        if ends_block and index + 1 < instruction_count:
            is_leader[index + 1] = True

    block_starts = [index for index in range(instruction_count) if is_leader[index]]
    block_of = {}
    block_end = {}
    for position, start in enumerate(block_starts):
        end = (block_starts[position + 1] if position + 1 < len(block_starts)
              else instruction_count)
        block_end[start] = end
        for index in range(start, end):
            block_of[index] = start

    successors = {start: set() for start in block_starts}
    for start in block_starts:
        end = block_end[start]
        if end == start:
            continue
        last_instruction = instructions[end - 1]
        is_branch = (last_instruction.opcode in dis.hasjrel
                    or last_instruction.opcode in dis.hasjabs)
        if is_branch:
            target_index = offset_to_index[last_instruction.argval]
            successors[start].add(block_of[target_index])
        is_terminal = last_instruction.opname in _TERMINAL_OPNAMES
        is_unconditional_jump = is_branch and last_instruction.opname in _UNCONDITIONAL_JUMP_OPNAMES
        falls_through = (not is_terminal) and (not is_unconditional_jump) and end < instruction_count
        if falls_through:
            successors[start].add(block_of[end])

    return block_of, block_end, successors, block_starts


def _reaching_definitions(block_end, successors, block_starts, positions):
    """Standard forward reaching-definitions dataflow, restricted to ONE
    local's own def/use positions (as produced by `_check_local_domain`).

    `positions` is a list of `(instruction_index, role)` with `role` in
    `("def", "use")` - every `STORE_FAST`/`DELETE_FAST` of the one local
    being examined is a "def", every `LOAD_FAST` of it is a "use".

    Returns `{use_index: frozenset(def_index, ...)}`: for each use, exactly
    which stores could be the one whose value it actually reads, over every
    possible path through the (already shared, already verified identical)
    control flow. An empty set at a use means that use is not reachable from
    any store on some path - the OLD program would raise `UnboundLocalError`
    there, so a split imposes no constraint at that use (see
    `_check_local_domain`: whichever new name it ends up spelled with, the
    old program never produced a real value for it to disagree about).
    """
    defs = {index for index, role in positions if role == "def"}
    uses = {index for index, role in positions if role == "use"}
    touched_by_block = {}
    for start in block_starts:
        touched_by_block[start] = [index for index in range(start, block_end[start])
                                   if index in defs or index in uses]

    predecessors = {start: set() for start in block_starts}
    for start, targets in successors.items():
        for target in targets:
            predecessors[target].add(start)

    reaching_in = {start: frozenset() for start in block_starts}
    reaching_out = {start: frozenset() for start in block_starts}
    reach_at_use = {}
    changed = True
    while changed:
        changed = False
        for start in block_starts:
            incoming = frozenset()
            for predecessor in predecessors[start]:
                incoming = incoming | reaching_out[predecessor]
            if incoming != reaching_in[start]:
                reaching_in[start] = incoming
                changed = True
            current = reaching_in[start]
            for index in touched_by_block[start]:
                if index in defs:
                    current = frozenset((index,))
                else:
                    reach_at_use[index] = current
            if current != reaching_out[start]:
                reaching_out[start] = current
                changed = True
    return reach_at_use


def _check_local_domain(pairs, old_code, new_code, old_instructions, label):
    """`pairs` is `(instruction_index, opname, old_name, new_name)` for every
    LOAD_FAST/STORE_FAST/DELETE_FAST in a stream already proven identical
    apart from which slot each one touches, in instruction order.

    Accepts:
      - a clean bijection - every old local maps to exactly one new local,
        and every new local comes from exactly one old local. An ordinary
        rename, in any order, including a permutation.
      - a SPLIT - one old local maps to more than one new local - PROVIDED:
        none of the new locals it split into is also shared with a different
        old local (that would be a merge, see below); the old local is not a
        parameter (its value is bound once, by the caller - a parameter is
        Tier 2 territory to begin with, see `renamed_parameters`, and is not
        something this file's def/use analysis can see the calling
        convention behind anyway); the function has no
        try/except/finally/with anywhere in it (see `_build_control_flow`'s
        docstring for why); and, restricted to that one old local's own
        def/use positions, every value a `LOAD_FAST` could actually read
        (its reaching definitions - `_reaching_definitions`) was written
        under the SAME new name it is read under. That last condition is
        exactly "the two meanings never actually shared a value" - which is
        what makes splitting the slot instead of merely renaming it
        behaviour-preserving, and what a real behaviour change hidden inside
        a plausible-looking split fails.

    Refuses:
      - a MERGE - a new local receiving from more than one old local -
        outright. Not one of the four hazards this file was built to make
        provable, and NAMING_PLAN.md's own advice for that case ("grep the
        enclosing function for the new name before using it") is to avoid it
        rather than rely on a proof, so this file does not attempt one.
      - a split of a parameter's own slot.
      - a split anywhere inside a try/except/finally/with.
      - a split where some reaching definition crosses into a use spelled
        with a DIFFERENT new name - the value flow that made the two
        occurrences one variable in the first place, severed.
    """
    problems = []
    old_to_new = collections.defaultdict(set)
    new_to_old = collections.defaultdict(set)
    for _, _, old_name, new_name in pairs:
        old_to_new[old_name].add(new_name)
        new_to_old[new_name].add(old_name)

    merged_names = sorted(new_name for new_name, old_names in new_to_old.items()
                          if len(old_names) > 1)
    if merged_names:
        for new_name in merged_names:
            problems.append(
                "%s: local '%s' now holds what used to be %d separate locals "
                "(%s) - that is a MERGE, not a rename, and this tool does not "
                "attempt to prove one safe (NAMING_PLAN.md's own advice is to "
                "pick a name that does not already exist in the function "
                "instead)" % (label, new_name, len(new_to_old[new_name]),
                             sorted(new_to_old[new_name])))
        return problems

    split_names = sorted(old_name for old_name, new_names in old_to_new.items()
                         if len(new_names) > 1)
    if not split_names:
        return problems

    if old_code.co_exceptiontable or new_code.co_exceptiontable:
        for old_name in split_names:
            problems.append(
                "%s: local '%s' is split into %s, but the function has a "
                "try/except/finally or a with block - a split cannot be "
                "proven safe there by this tool (see _build_control_flow); "
                "verify it by hand or leave the name alone"
                % (label, old_name, sorted(old_to_new[old_name])))
        return problems

    parameter_count = (old_code.co_argcount + old_code.co_kwonlyargcount
                      + bool(old_code.co_flags & 0x4)   # CO_VARARGS  (*args)
                      + bool(old_code.co_flags & 0x8))  # CO_VARKEYWORDS (**kwargs)
    parameter_names = set(old_code.co_varnames[:parameter_count])

    block_of, block_end, successors, block_starts = _build_control_flow(old_instructions)

    new_name_at = {index: new_name for index, _, _, new_name in pairs}
    positions_by_old_name = collections.defaultdict(list)
    for index, opname, old_name, _ in pairs:
        role = "def" if opname in ("STORE_FAST", "DELETE_FAST") else "use"
        positions_by_old_name[old_name].append((index, role))

    for old_name in split_names:
        if old_name in parameter_names:
            problems.append(
                "%s: parameter '%s' is split into %s - a parameter's value "
                "comes from the caller once, at entry; splitting it is a "
                "real change, not a rename" % (label, old_name, sorted(old_to_new[old_name])))
            continue
        reach_at_use = _reaching_definitions(block_end, successors, block_starts,
                                             positions_by_old_name[old_name])
        crosses_a_real_edge = any(
            new_name_at[def_index] != new_name_at[use_index]
            for use_index, def_indices in reach_at_use.items()
            for def_index in def_indices)
        if crosses_a_real_edge:
            problems.append(
                "%s: '%s' is split into %s, but a value written under one of "
                "those new names is read under another - that is a real "
                "behaviour change, not a rename"
                % (label, old_name, sorted(old_to_new[old_name])))
    return problems


def _check_free_domain(old_instructions, new_instructions, label):
    """Captured-variable slots: MAKE_CELL, LOAD_DEREF, STORE_DEREF,
    DELETE_DEREF, LOAD_CLASSDEREF and LOAD_CLOSURE. Same bijection check as
    `_check_local_domain`'s base case, with no split or merge support - but
    NOT the same naive position-for-position pairing, because one of these
    opcodes lies about order.

    MAKE_CELL is emitted once per cellvar this code object OWNS, in
    DECLARATION order (matching the source, e.g. parameter order) - reliable.
    LOAD_DEREF/STORE_DEREF/DELETE_DEREF/LOAD_CLASSDEREF are emitted in
    SOURCE-READ order wherever a captured name is actually used - also
    reliable. LOAD_CLOSURE is different: it builds a NESTED function's
    closure tuple, so it is emitted in THAT NESTED FUNCTION's own
    alphabetically-sorted freevar order - the same "co_cellvars is sorted
    alphabetically" fact that makes the raw-slot-index hazard real in the
    first place, except here it also scrambles which POSITION each name
    appears at in THIS function's own bytecode. Naively pairing LOAD_CLOSURE
    by position, alongside the reliable opcodes, reproduces exactly the
    original bug this file exists to fix: renaming only one captured local
    can appear to "split" or "merge" several others purely because their
    LOAD_CLOSURE instructions traded places (confirmed against CPython
    3.11.15: renaming a single cellvar changed which name every OTHER
    LOAD_CLOSURE position referred to, while every MAKE_CELL stayed put).

    So LOAD_CLOSURE is pulled out and checked separately, against the
    bijection already established from the reliable opcodes: for every old
    name with a KNOWN new name, the multiset of LOAD_CLOSURE names built here
    is checked to actually contain that new name once. What is left over -
    names captured from an outer scope, passed through into a further-nested
    closure, and never otherwise read in THIS function - has no reliable
    ordering evidence available anywhere in this code object, and can only be
    checked by total COUNT on both sides. That is a real, narrow gap: two
    such passthrough-only names could in principle be swapped without this
    check noticing. It is also a corner CPython's own parser makes exceedingly
    rare in practice (a function that captures a name purely to hand it
    further down, never touching it itself), it is not one of the four
    hazards this file was built to make provable, and getting it wrong here
    can only produce a false ACCEPT of an already-exotic pattern, never a
    false refusal of an ordinary rename - so it is accepted as a documented
    boundary rather than solved.
    """
    reliable_pairs = []
    old_load_closure = []
    new_load_closure = []
    for old_instruction, new_instruction in zip(old_instructions, new_instructions):
        if old_instruction.opname in _ORDER_UNRELIABLE_FREE_OPNAMES:
            old_load_closure.append(old_instruction.argval)
            new_load_closure.append(new_instruction.argval)
        elif old_instruction.opname in _RELIABLE_FREE_OPNAMES:
            reliable_pairs.append((old_instruction.argval, new_instruction.argval))

    old_to_new = collections.defaultdict(set)
    new_to_old = collections.defaultdict(set)
    for old_name, new_name in reliable_pairs:
        old_to_new[old_name].add(new_name)
        new_to_old[new_name].add(old_name)

    problems = []
    split = sorted(name for name, targets in old_to_new.items() if len(targets) > 1)
    merged = sorted(name for name, sources in new_to_old.items() if len(sources) > 1)
    if split or merged:
        problems.append(
            "%s: a captured (cell/free) variable's slot usage is not a plain "
            "rename - split: %s, merged: %s. This tool does not attempt to "
            "prove a captured-variable split or merge safe."
            % (label, split, merged))
        return problems

    known = {old_name: next(iter(targets)) for old_name, targets in old_to_new.items()}
    new_counter = collections.Counter(new_load_closure)
    undetermined_old_count = 0
    for old_name in old_load_closure:
        new_name = known.get(old_name)
        if new_name is None:
            undetermined_old_count += 1
            continue
        if new_counter[new_name] > 0:
            new_counter[new_name] -= 1
        else:
            problems.append(
                "%s: a nested closure built here should carry the renamed "
                "'%s' -> '%s', but '%s' is not among what the new code "
                "closes over there" % (label, old_name, new_name, new_name))
    remaining_new_total = sum(new_counter.values())
    if remaining_new_total != undetermined_old_count:
        problems.append(
            "%s: a variable passed through into a nested closure without "
            "being read here directly changed in a way this tool cannot "
            "resolve by name alone - verify by hand" % label)
    return problems


def _compare_code_pair(old_code, new_code, label, name_may_differ, problems, matched_pairs):
    """Recursively compare one matched pair of code objects.

    Appends to `problems` (every difference that is NOT a rename) and to
    `matched_pairs` (every pair this walk was able to line up, whether or
    not it later turned out to differ - `renamed_parameters` needs the full
    list, not just the clean ones, so a renamed nested helper's own
    parameters still get checked).

    `name_may_differ` is True exactly when `old_code`/`new_code` were paired
    up POSITIONALLY rather than by name - i.e. when their shared parent is a
    function/lambda/comprehension body (`_is_fast_scope`), so this code
    object is only ever reachable through a local inside that parent, never
    from outside it. That local is already covered by the checks above; the
    code object's OWN name is then free to change too (hazard 4: a nested
    `def`'s name is not part of any interface). A FIXED syntactic name
    (`<listcomp>` and friends) is the one exception even then - see
    `_fixed_syntactic_name`.
    """
    _assert_known_variable_opcodes(old_code, label)
    _assert_known_variable_opcodes(new_code, label)

    name_is_fixed = (_fixed_syntactic_name(old_code.co_name)
                     or _fixed_syntactic_name(new_code.co_name))
    if (not name_may_differ) or name_is_fixed:
        if old_code.co_name != new_code.co_name:
            problems.append(
                "%s: renamed %s -> %s - a module-level name, a class "
                "attribute name, or a comprehension/lambda's fixed spelling "
                "is part of the interface or the syntax, not a local; this "
                "is Tier 2 or 3, verify it another way"
                % (label, old_code.co_name, new_code.co_name))

    matched_pairs.append((label, old_code, new_code))

    old_instructions = _instructions(old_code)
    new_instructions = _instructions(new_code)
    old_stream = _normalised_stream(old_instructions)
    new_stream = _normalised_stream(new_instructions)

    if old_stream != new_stream:
        problems.append("%s: the BYTECODE changed - this is not a rename, "
                        "it is a behaviour change" % label)
        for index in range(min(len(old_stream), len(new_stream))):
            if old_stream[index] != new_stream[index]:
                problems.append(
                    "%s: first difference at instruction #%d: %s vs %s"
                    % (label, index, old_stream[index], new_stream[index]))
                break
        if len(old_stream) != len(new_stream):
            problems.append("%s: instruction count changed (%d -> %d)"
                            % (label, len(old_stream), len(new_stream)))
    else:
        # Streams match position-for-position, so the (index, opname,
        # old_argval, new_argval) below are genuinely paired occurrences of
        # the same instruction, not a coincidence.
        local_pairs = []
        for index, (old_instruction, new_instruction) in enumerate(
                zip(old_instructions, new_instructions)):
            if old_instruction.opname in _LOCAL_OPNAMES:
                local_pairs.append((index, old_instruction.opname,
                                    old_instruction.argval, new_instruction.argval))
        problems.extend(_check_local_domain(local_pairs, old_code, new_code,
                                            old_instructions, label))
        problems.extend(_check_free_domain(old_instructions, new_instructions, label))

    old_consts = _consts_without_code(old_code)
    new_consts = _consts_without_code(new_code)
    if old_consts != new_consts:
        # NAME WHAT MOVED, BECAUSE THERE ARE TWO VERY DIFFERENT CAUSES AND
        # THE READER CANNOT TELL THEM APART FROM A BARE "a constant changed".
        #
        # The first is the one this message was written for: somebody edited
        # a literal or a docstring in the same commit as a rename, and the
        # fix is to separate them.
        #
        # The second is not an edit at all. A parameter carrying a PEP 484
        # annotation has its NAME stored as a string constant in the
        # ENCLOSING scope, to be built into `__annotations__`, so renaming
        # `def f(k: str)` to `def f(node_id: str)` moves the enclosing
        # module's co_consts even though nothing was edited but the name.
        # Verified directly: two modules differing only in that parameter's
        # name compile to enclosing co_consts of ('k', 'return') and
        # ('node_id', 'return'); without the annotation both are empty.
        # This one is a hole in the proof, exactly like the keyword-argument
        # hole, and it will widen as annotations spread through this
        # codebase.
        #
        # Printing the difference tells the two apart instantly: a pair of
        # identifiers is the annotation case, a sentence is the prose case.
        removed = [const for const in old_consts if const not in new_consts]
        added = [const for const in new_consts if const not in old_consts]

        def _shown(values):
            rendered = [repr(value)[:60] for value in values[:4]]
            if len(values) > 4:
                rendered.append("... and %d more" % (len(values) - 4))
            return ", ".join(rendered) or "(none)"

        problems.append(
            "%s: a CONSTANT changed - gone: %s / added: %s. Either a literal "
            "or a docstring was edited, in which case make prose edits in a "
            "separate commit, OR an ANNOTATED parameter was renamed, which "
            "stores its name as a constant in the enclosing scope and is a "
            "known hole in this proof rather than a real change. A pair of "
            "bare identifiers means the second."
            % (label, _shown(removed), _shown(added)))

    if old_code.co_names != new_code.co_names:
        gone = sorted(set(old_code.co_names) - set(new_code.co_names))
        added = sorted(set(new_code.co_names) - set(old_code.co_names))
        problems.append(
            "%s: an ATTRIBUTE or GLOBAL changed, not a local - removed %s, "
            "added %s. That is Tier 2 or 3; verify it another way."
            % (label, gone or "nothing", added or "nothing"))

    old_children = _nested_children(old_code)
    new_children = _nested_children(new_code)
    if len(old_children) != len(new_children):
        problems.append(
            "%s: %d nested function/class/comprehension body(ies) became %d "
            "- something was added or removed, not just renamed"
            % (label, len(old_children), len(new_children)))
        return

    if _is_fast_scope(old_code) or _is_fast_scope(new_code):
        # A function/lambda/comprehension body: its own nested definitions
        # are only ever reachable through a local name INSIDE it (already
        # covered above), never from outside, so they are paired up
        # positionally and their own co_name may be part of the rename.
        for index, (old_child, new_child) in enumerate(zip(old_children, new_children)):
            child_label = "%s[%d]" % (label, index)
            _compare_code_pair(old_child, new_child, child_label, True,
                              problems, matched_pairs)
    else:
        # A module or a class body: children are top-level defs/classes or
        # methods, reachable from OUTSIDE by name (an import, or
        # `ClassName.method`), so the name itself is part of the interface
        # and children are matched BY NAME - which also lets sibling defs be
        # reordered harmlessly, something a rename commit sometimes does in
        # passing.
        old_by_name = collections.defaultdict(list)
        new_by_name = collections.defaultdict(list)
        for child in old_children:
            old_by_name[child.co_name].append(child)
        for child in new_children:
            new_by_name[child.co_name].append(child)
        only_before = sorted(set(old_by_name) - set(new_by_name))
        only_after = sorted(set(new_by_name) - set(old_by_name))
        for name in only_before:
            problems.append("%s: function or class disappeared or was "
                            "renamed: %s" % (label, name))
        for name in only_after:
            problems.append("%s: function or class appeared or was "
                            "renamed: %s" % (label, name))
        for name in sorted(set(old_by_name) & set(new_by_name)):
            old_list, new_list = old_by_name[name], new_by_name[name]
            if len(old_list) != len(new_list):
                problems.append("%s: %s defined %d time(s) before, %d after"
                                % (label, name, len(old_list), len(new_list)))
                continue
            for index, (old_child, new_child) in enumerate(zip(old_list, new_list)):
                child_label = "%s.%s" % (label, name)
                if len(old_list) > 1:
                    child_label += "#%d" % index
                _compare_code_pair(old_child, new_child, child_label, False,
                                  problems, matched_pairs)


def _compare_tree(before_code, after_code, filename):
    """Shared by `compare` and `renamed_parameters`: one tree walk, so both
    see exactly the same matched pairs instead of two independently-matched
    trees drifting apart."""
    problems = []
    matched_pairs = []
    _compare_code_pair(before_code, after_code, "<module>", False,
                       problems, matched_pairs)
    return problems, matched_pairs


def compare(before_source, after_source, filename):
    """Return a list of differences that are NOT a local rename."""
    try:
        before_code = compile_source(before_source, filename)
    except SyntaxError as exc:
        return ["the OLD version does not compile: %s" % exc]
    try:
        after_code = compile_source(after_source, filename)
    except SyntaxError as exc:
        return ["the NEW version does not compile: %s" % exc]
    problems, _ = _compare_tree(before_code, after_code, filename)
    return problems


def renamed_parameters(before_source, after_source, filename):
    """Renamed locals that are also parameters: callers may pass by keyword."""
    before_code = compile_source(before_source, filename)
    after_code = compile_source(after_source, filename)
    _, matched_pairs = _compare_tree(before_code, after_code, filename)
    flagged = []
    for label, old_code, new_code in matched_pairs:
        count = old_code.co_argcount + old_code.co_kwonlyargcount
        for old_arg, new_arg in zip(old_code.co_varnames[:count],
                                    new_code.co_varnames[:count]):
            if old_arg != new_arg:
                flagged.append("%s: parameter %s -> %s" % (label, old_arg, new_arg))
    return flagged


def git_show(ref, path):
    result = subprocess.run(["git", "show", "%s:%s" % (ref, path)],
                            capture_output=True, text=True, cwd=ROOT)
    return result.stdout if result.returncode == 0 else None


def python_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "sim")):
        dirnames[:] = [dirname for dirname in dirnames if dirname != "__pycache__"]
        for filename in filenames:
            if filename.endswith(".py"):
                out.append(os.path.relpath(os.path.join(dirpath, filename), ROOT))
    return sorted(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ref", help="git ref to compare the working tree against")
    parser.add_argument("paths", nargs="*",
                        help="files to check; default is every .py under sim/")
    parser.add_argument("--check-params", action="store_true",
                        help="also list renamed parameters, whose callers may "
                             "pass them by keyword")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    paths = args.paths or python_files()
    checked = skipped = 0
    failures = []
    parameter_notes = []

    for path in paths:
        before_source = git_show(args.ref, path)
        if before_source is None:
            skipped += 1
            if args.verbose:
                print("  skip (not in %s)  %s" % (args.ref, path))
            continue
        with open(os.path.join(ROOT, path)) as handle:
            after_source = handle.read()
        if before_source == after_source:
            skipped += 1
            if args.verbose:
                print("  unchanged         %s" % path)
            continue
        checked += 1
        problems = compare(before_source, after_source, path)
        if problems:
            failures.append((path, problems))
            print("  FAIL              %s" % path)
            for problem in problems[:6]:
                print("        %s" % problem)
        else:
            print("  proven rename     %s" % path)
            if args.check_params:
                for note in renamed_parameters(before_source, after_source, path):
                    parameter_notes.append("%s  %s" % (path, note))

    print()
    print("%d changed file(s) checked, %d unchanged or absent, %d failed"
          % (checked, skipped, len(failures)))
    if parameter_notes:
        print()
        print("PARAMETERS were renamed in these places. The bytecode proof does")
        print("NOT cover them: a caller writing f(s=...) breaks and this tool")
        print("cannot see it. Check the call sites by hand.")
        for note in parameter_notes:
            print("   %s" % note)
    if not checked and not failures:
        print("Nothing changed against %s - nothing to prove." % args.ref)
    elif not failures:
        print()
        print("PROVEN: every change is a local-variable rename. Identical")
        print("bytecode, identical attributes and globals, identical constants.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
