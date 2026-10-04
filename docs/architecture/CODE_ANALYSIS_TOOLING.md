# Code analysis tooling

What this repository uses to check its own maintainability, which parts are
hand-written and why, and which established library sits under each one.
Every number below carries the command that produced it, per CLAUDE.md
section 6; run the command rather than trust the number if it matters to you.

The stakeholder's instruction that produced this document: "It looks like the
scanner was hand wrote, can we look for any libraries/tools to help us with
making this more maintainable. Reinventing the wheel often means we lose good
tools." What follows is the answer, tool by tool.

---

## 1. The hand-written scanner

`sim/code_health.py` (naming, duplication, complexity and miscellaneous
scans) and `sim/prove_rename_safe.py` were removed. Recover them with
`git show 97473f1:sim/code_health.py` and
`git show 97473f1:sim/prove_rename_safe.py`. What remains is `ruff`,
`pylint` and `rope`, described below.

---

## 2. `ruff.toml`: what changed and why

`ruff.toml` now enables four more rules beyond `F`: `B905`
(zip-without-explicit-strict, 19 findings), `B007`
(unused-loop-control-variable, 16), `SIM115`
(open-file-with-context-handler, 52), `RUF100` (unused-noqa, 84 real /
85 measured under `--isolated`, see below). Each is selected individually,
not by family, and the file's own comments carry the full reasoning
alongside each one, per CLAUDE.md section 6. Counts:
`python3 -m ruff check sim/ --statistics` (uses the real, non-isolated
config).

Rejected, and why, recorded in `ruff.toml` itself so the next agent does not
re-propose them blind: `N*` (checks casing, not length - `pylint` in section 3 is
the real answer to the naming problem), `PL*` (627 findings, 627 of them
`PLR2004` - one deliberate decision, comparing computed quantities to
thresholds is this simulation's whole job), `ARG*` (178 findings, dominated
by the CLI dispatcher's uniform `cmd_something(a)` signature - another one
deliberate decision, the same shape already recorded for `F403`/`F405`),
`PERF401` (54 findings, an unmeasured micro-optimisation with no evidence
this codebase's loops are a bottleneck), `C90` (complexity is not gated here). Also rejected:
the REST of `B` and `SIM` beyond the two rules taken from each -
`SIM300` (yoda-conditions) in particular actively fights this codebase's own
convention of writing numeric bounds checks as `0.0 < value`
(interval-notation order, used throughout `sim/world/`), so family-level
selection was rejected in favour of naming the two rules worth having from
each family individually.

**One caveat on the `RUF100` count.** `RUF100`'s answer depends on which
OTHER rules are actually enabled, because it reports a `noqa` comment as
unused only when nothing selected would have fired there.
`ruff check --isolated --select RUF100` (ignoring this repo's real config)
reports 85 - inflated, because under `--isolated` nothing else is enabled
either, so every `# noqa: F401` in the tree looks unused regardless of
whether it is really guarding something. The number that matters is under
the real config, where `F` (which includes `F401`) is also active:
`python3 -m ruff check --select F,RUF100 sim/ --statistics` → 84 (`F401`'s
own 78 alongside it, `F811`'s 2 pre-existing). `ruff.toml`'s comment states
this explicitly so nobody re-quotes the isolated number as the real one.

**Effect on the suite.** `sim/tests/test_static_checks.py` (the
`static_checks` topic) hardcodes `--isolated --select F821` and does not
read `ruff.toml`'s `[lint] select` at all, so none of these four additions
change what that topic checks or its pass/fail. Verified:
`python3 -m sim.tests --only static_checks` → `2 checks,
0 failures`, both before and after this change. The only thing this change affects is what a person or agent sees running
plain `ruff check sim/` by hand.

---

## 3. `.pylintrc`: the naming-sweep worklist

New file, repository root. Enables only `invalid-name` (`C0103`) - every
other `pylint` check is off, on purpose, so a naming sweep is not also
buried under style opinions about docstrings or return counts. The regex
(`[a-zA-Z_][a-zA-Z0-9_]{2,}$`) enforces a MINIMUM length of three characters
and no maximum, applied to variables, arguments, inline (for/with/except)
bindings, attributes, class attributes, constants, methods, functions,
classes and modules alike - deliberately not the default casing-convention
patterns, both because this repo is not being asked to change its casing
style and because the default `method-rgx`/`function-rgx` broke on this
codebase's own `ast.NodeVisitor` subclasses (they use CamelCase
`visit_FunctionDef`-style names). `good-names=i,x,y,_` matches CLAUDE.md's
naming exemptions, but is not role-aware: it exempts `i`/`x`/`y` everywhere,
not only as a loop index or coordinate pair.

Run it: `python3 -m pylint sim/`; it lists a `file:line` for every short name.

---

## 4. Renaming: `rope`, tried and adopted as the pipeline

CLAUDE.md section 7 and this repository's own history are emphatic that
regex-based renaming corrupts this codebase (it is 30-50% prose by line; an
earlier attempt at a regex rename was thrown away). The rename prover (`sim/prove_rename_safe.py`, since removed)
proved a rename was safe AFTER it happened, by bytecode comparison, and
documented its own hole: it could not certify a parameter rename, because a
caller passing that parameter by keyword breaks invisibly to a bytecode
diff. A refactoring tool that performs the rename correctly in the first
place, using real scope analysis rather than text matching, is a different
and better answer than proving one after the fact.

**`rope` (1.14.0, already installed:** `python3 -c "import rope"`**) was
tried on a real local in a scratch copy of this repository** (`cp -a`, never
the real checkout) **and the pipeline works end to end:**

    # sim/geography/geography.py:270, a real function-local `ab` used three
    # times across a for-loop body (float(cast(...)), a comparison, two
    # uses in the accumulator) - a genuine Tier-1 case from this codebase,
    # not a constructed one.
    from rope.base.project import Project
    from rope.refactor.rename import Rename
    project = Project('.')
    resource = project.get_resource('sim/geography/geography.py')
    renamer = Rename(project, resource, <offset of ab>)
    project.do(renamer.get_changes('mineral_abundance'))
    # -> all three occurrences renamed, nothing else in the 300-line file touched

**And on the case the removed rename prover said it could not cover -** a
parameter renamed where a caller passes it by keyword - `rope` gets it
right where a text-based tool structurally cannot:

    # definer.py: def compute_total(rev, yr, cap): ...
    # caller.py:  compute_total(rev=10, yr=2024, cap=5)
    # rename `yr` -> `year` via rope.refactor.rename.Rename, same API as above
    # result, caller.py: compute_total(rev=10, year=2024, cap=5)
    #   - the keyword call site was found and updated correctly, across files,
    #     because rope resolves the parameter binding rather than matching text.

**Verdict: workable, and worth using for both Tier 1 and Tier 2 renames in
the coming naming sweep.** `rope` builds a real name-resolution index over
the project rather than matching text, so it does not have the failure mode
CLAUDE.md warns about (a regex rename corrupting prose that happens to
contain the same characters) and it follows parameter renames through
keyword call sites. The suggested pipeline for the sweep: perform each
rename with `rope.refactor.rename.Rename`, then run the test suite.

`libcst` (1.x, already installed) was not tried beyond this, because `rope`
worked cleanly on both the Tier-1 and Tier-2 cases above with no rough
edges - `libcst` is lower-level (a concrete-syntax-tree codemod toolkit; it
would require hand-writing the scope resolution `rope` already provides, via
its own `ScopeProvider` metadata) and there was no observed gap in `rope`'s
behaviour that would justify reaching for it. If a future rename case does
defeat `rope` - a dynamic attribute rename, a name rebuilt from a string,
something outside static scope analysis - `libcst`'s metadata providers are
the fallback worth trying next, not a second default choice.
