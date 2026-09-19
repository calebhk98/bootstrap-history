# Code analysis tooling

What this repository uses to check its own maintainability, which parts are
hand-written and why, and which established library sits under each one.
Every number below carries the command that produced it, per CLAUDE.md
section 8; run the command rather than trust the number if it matters to you.

The stakeholder's instruction that produced this document: "It looks like the
scanner was hand wrote, can we look for any libraries/tools to help us with
making this more maintainable. Reinventing the wheel often means we lose good
tools." What follows is the answer, tool by tool.

---

## 1. The four things `sim/code_health.py` checks, and what runs under each

`sim/code_health.py` is kept - the stakeholder was explicit ("We can keep the
handwritten one") - and it already composes two established libraries rather
than reimplementing them (`radon` for complexity, `ruff` for two import
checks; see its own module docstring). This section covers the two detectors
it does NOT get from a library: the naming scanner and the duplication
detector.

### 1.1 Short-identifier scanning: kept hand-written, `pylint` added alongside it

**What was tried.** `ruff`'s `N` family (`N812`, `N806`, `N816`, `N803`)
checks naming CONVENTION - snake_case, PascalCase - not LENGTH. It does not
see a two-character name as a problem at all, so it cannot answer CLAUDE.md
section 7's actual complaint. `pylint`'s `invalid-name` (`C0103`) can be given
a length-based regex instead of a convention one, and it separates
`Argument` from `Variable` from `Inline` from `Constant` as distinct
categories - which maps onto CLAUDE.md section 7's Tier 1 (a purely local
variable, provably safe to rename by `sim/prove_rename_safe.py`) / Tier 2 (a
parameter, or anything at module/class scope, needing a call-site check) more
closely than any other established tool found.

**What it took to make that usable.** `pylint`'s default `method-rgx` and
`function-rgx` also enforce casing convention, and this codebase's own
`ast.NodeVisitor` subclasses use Python's required `visit_FunctionDef`-style
CamelCase method names - so an early attempt at this config flagged 197
un-renameable framework method names as "doesn't conform to snake_case
naming style", pure noise unrelated to short identifiers. Loosening
`method-rgx`/`function-rgx`/`class-rgx` to length-only (see `.pylintrc`)
removed it entirely:

    python3 -m pylint sim/ --output-format=json | python3 -c \
      "import json,sys,collections; d=json.load(sys.stdin); \
       print(collections.Counter(x['message'].split()[0] for x in d).most_common())"
    # [('Argument', 451), ('Inline', 166), ('Variable', 127),
    #  ('Function', 2), ('Constant', 2), ('Attribute', 1), ('Class', 1)]
    # 750 total findings, zero Method findings.

**Verdict: keep both, for different jobs.** `sim/code_health.py --names`
(`python3 sim/code_health.py --names`) stays as the measurement tool: it is
the only one that implements CLAUDE.md section 7's exact exemption rule (`i`
only when it is a loop index by ROLE, `x`/`y` only when bound together as a
pair - see its own `_ScopeVisitor` docstring), it reports the Tier-1 share as
a trend to burn down (`record`/`check` against a baseline, the same shape as
`sim/perf_fingerprint.py`), and it is what the 4,972/3,813/3,759 reference
figures in CLAUDE.md section 7 are compared against.

`.pylintrc` (new, this repository's root) is the worklist: a `file:line` for
every short name, filterable by category (`Argument` findings are Tier 2,
`Variable`/`Inline` findings are Tier 1 candidates), runnable by anyone with
`python3 -m pylint sim/` and no knowledge of this codebase's own scanner.
CLAUDE.md section 7 says the naming sweep is coming next; this is the tool
for doing it, not just measuring it.

**The one real gap, recorded rather than hidden.** `pylint`'s `good-names`
(`i,x,y,_`, matching CLAUDE.md's exemptions exactly) is not role-aware: it
exempts `i`/`x`/`y` everywhere, not only when `i` is a loop index or `x`/`y`
are bound as a pair. `sim/code_health.py`'s scanner remains the precise
answer to "does this specific occurrence count"; `pylint` is the tool for
"where are they", accepting a slightly looser exemption in exchange for
being runnable today.

### 1.2 Duplication detection: kept hand-written, and here is the evidence

**The validation case.** `sim/code_health.py`'s duplication detector exists
because of one real bug: before `sim/engine/hazard_window.py` was extracted
(`git log --oneline --diff-filter=A -- sim/engine/hazard_window.py` →
`0de3976`, whose parent is `a3b05ef`), `FogMixin.knowledge_risk` in
`fog.py` and `SocietyMixin.hazard_timeline` in `society.py` each opened
`civ["hazards"]` and did the same window-arithmetic in a loop, with
different local variable names. A correct detector has to find that pair
across two files despite the renamed variables. It does:

    git show a3b05ef:sim/engine/fog.py > /tmp/fog.py
    git show a3b05ef:sim/engine/society.py > /tmp/society.py
    # then, from a checkout with sim.code_health imported and ROOT pointed
    # at the directory holding both:
    ch.duplication_report(["sim/engine/fog.py", "sim/engine/society.py"])
    # -> a cluster: distinct_versions=1, mean_cross_version_similarity=1.0,
    #    fog.py:324-330 / society.py:3021-3027 (the exact pre-extraction lines)

**What `pylint`'s `duplicate-code` (R0801) does with the same case.**

    python3 -m pylint --disable=all --enable=duplicate-code /tmp/fog.py /tmp/society.py
    # finds it: ==fog:[322:330] / ==society:[3019:3027], "Similar lines in 2 files"

`pylint` finds the real, historical case too. But two follow-up tests show
why it is not a replacement:

**Test 1: intra-file duplication.** `pylint`'s `duplicate-code` only ever
compares DIFFERENT files - "Similar lines in %s files" requires at least two
modules by construction.

    python3 -m pylint --disable=all --enable=duplicate-code /tmp/society.py
    # alone: "Your code has been rated at 10.00/10" - nothing found

`sim/code_health.py`'s own detector, run against the same single file,
found five more clusters entirely WITHIN `society.py` - including one
206-node block repeated at eight different sites in the same file. `pylint`
cannot see any of that, structurally, no matter how it is configured.

**Test 2: renamed variables.** `pylint`'s `duplicate-code` compares TEXT
lines. Two blocks that are the identical structure with different variable
names do not match:

    # a.py and b.py: same 8-line loop, every local variable renamed
    # (hazard/yrs/year_start/year_end/bar -> event/window/start/end/qux)
    python3 -m pylint --disable=all --enable=duplicate-code a.py b.py
    # "Your code has been rated at 10.00/10" - nothing found

`sim/code_health.py`'s detector, on the same fixture, finds it as an exact
structural match (`distinct_versions=1, mean_cross_version_similarity=1.0`)
because it normalises the AST before comparing - `_normalize()` erases a
`Name`'s own spelling on purpose (see that function's docstring). This is
not a corner case for this project: CLAUDE.md section 7 exists because this
codebase is thick with exactly this kind of renamed-but-structurally-
identical code, and a detector that a rename defeats is not useful here.

**Verdict: keep the hand-written detector. `jscpd` (also considered per the
stakeholder's brief) is not installed in this environment and was not
evaluated further once `pylint`'s two structural gaps were confirmed** -
`jscpd`, like `pylint`, is a token/text-based detector, not an AST-normalising
one, so it would be expected to share the renamed-variable gap; nobody
should treat that expectation as measured, since it was not run here.

Today's numbers on the real tree, for reference (`python3 sim/code_health.py
--duplication`): 3,522 candidate blocks, 137 clusters (25 exact clones, 112
showing divergence into more than one version).

### 1.3 Complexity and size: already a library, unchanged

`sim/code_health.py --complexity` already imports `radon.complexity` and
`radon.raw` directly (see its own docstring, section "WHAT THIS COMPOSES
WITH"). Nothing to replace. `xenon` (also installed:
`python3 -m xenon --version`) is the same `radon` engine wrapped as a CI
gate rather than a report; it was run for comparison
(`python3 -m xenon --max-absolute C sim/`) and finds the same functions
`code_health.py` does, because it is the same complexity metric underneath.
Not adopted as a second tool: `sim/code_health.py` already picked and
recorded its own threshold (15, `COMPLEXITY_THRESHOLD` in that file) with a
`record`/`check` burndown; `xenon`'s job (fail a build over a threshold)
would duplicate that with a second config to keep in sync, for no
capability `code_health.py` does not already have as a report. Today's
count, for reference: `python3 sim/code_health.py --complexity` → 65
functions above cyclomatic complexity 15.

### 1.4 Miscellaneous (`sim/code_health.py --misc`): already libraries, unchanged

Unused imports and late imports already shell out to `ruff` (`F401`,
`E402` - see that file's docstring). Long-parameter-list and the
`getattr(self, "name", default)` lazy-field-read detector are both small,
project-specific AST walks with no established-library equivalent found:
`pylint`'s `too-many-arguments` (`R0913`) covers the first (see §2 for a
side-by-side), but the lazy-`getattr` check is specific enough to this
codebase's own pattern - a save-compatibility field read through `getattr`
rather than a plain attribute access - that no general-purpose tool
targets it; it stays hand-written and labelled as such.

---

## 2. `ruff.toml`: what changed and why

`ruff.toml` now enables four more rules beyond `F`: `B905`
(zip-without-explicit-strict, 19 findings), `B007`
(unused-loop-control-variable, 16), `SIM115`
(open-file-with-context-handler, 52), `RUF100` (unused-noqa, 84 real /
85 measured under `--isolated`, see below). Each is selected individually,
not by family, and the file's own comments carry the full reasoning
alongside each one, per CLAUDE.md section 8. Counts:
`python3 -m ruff check sim/ --statistics` (uses the real, non-isolated
config).

Rejected, and why, recorded in `ruff.toml` itself so the next agent does not
re-propose them blind: `N*` (checks casing, not length - `pylint` in §1.1 is
the real answer to the naming problem), `PL*` (627 findings, 627 of them
`PLR2004` - one deliberate decision, comparing computed quantities to
thresholds is this simulation's whole job), `ARG*` (178 findings, dominated
by the CLI dispatcher's uniform `cmd_something(a)` signature - another one
deliberate decision, the same shape already recorded for `F403`/`F405`),
`PERF401` (54 findings, an unmeasured micro-optimisation with no evidence
this codebase's loops are a bottleneck), `C90` (would give the codebase two
disagreeing complexity thresholds - `code_health.py` already has one, at
15, chosen and recorded there; ruff's mccabe default is 10). Also rejected:
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
`python3 sim/test_regressions.py --only static_checks` → `2 checks,
0 failures`, both before and after this change. `sim/code_health.py --misc`
also passes its own explicit `--select` flags to `ruff` (`F401`, `E402`)
that override `ruff.toml`'s list the same way, so it is likewise unaffected.
The only thing this change affects is what a person or agent sees running
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
codebase's own `ast.NodeVisitor` subclasses (§1.1). `good-names=i,x,y,_`
matches CLAUDE.md section 7's exemptions exactly, with the role-unawareness
gap recorded in §1.1.

Run it: `python3 -m pylint sim/`. 750 findings today
(`Argument` 451, `Inline` 166, `Variable` 127, `Function` 2, `Constant` 2,
`Attribute` 1, `Class` 1) - command above, output piped through the
`collections.Counter` one-liner in §1.1 for the breakdown.

---

## 4. Renaming: `rope`, tried and adopted as the pipeline

CLAUDE.md section 7 and this repository's own history are emphatic that
regex-based renaming corrupts this codebase (it is 30-50% prose by line; an
earlier attempt at a regex rename was thrown away). `sim/prove_rename_safe.py`
proves a rename was safe AFTER it happens, by bytecode comparison, and
documents its own hole: it cannot certify a parameter rename, because a
caller passing that parameter by keyword breaks invisibly to a bytecode
diff. A refactoring tool that performs the rename correctly in the first
place, using real scope analysis rather than text matching, is a different
and better answer than proving one after the fact.

**`rope` (1.14.0, already installed:** `python3 -c "import rope"`**) was
tried on a real local in a scratch copy of this repository** (`cp -a`, never
the real checkout) **and the pipeline works end to end:**

    # sim/engine/geography.py:270, a real function-local `ab` used three
    # times across a for-loop body (float(cast(...)), a comparison, two
    # uses in the accumulator) - a genuine Tier-1 case from this codebase,
    # not a constructed one.
    from rope.base.project import Project
    from rope.refactor.rename import Rename
    project = Project('.')
    resource = project.get_resource('sim/engine/geography.py')
    renamer = Rename(project, resource, <offset of ab>)
    project.do(renamer.get_changes('mineral_abundance'))
    # -> all three occurrences renamed, nothing else in the 300-line file touched

    python3 sim/prove_rename_safe.py --verbose HEAD sim/engine/geography.py
    # -> "PROVEN: every change is a local-variable rename. Identical
    #     bytecode, identical attributes and globals, identical constants."
    #    1 changed file(s) checked, 0 unchanged or absent, 0 failed

**And on the case `prove_rename_safe.py` itself says it cannot cover -** a
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
contain the same characters) and it extends past what
`prove_rename_safe.py` alone can certify (parameter renames, followed
through keyword call sites). The suggested pipeline for the sweep: perform
each rename with `rope.refactor.rename.Rename`, then run
`sim/prove_rename_safe.py` on the touched files as a second, independent
proof for the Tier-1 (local) part of the change - belt and braces, at
negligible cost since both tools are already fast on a file at a time.

`libcst` (1.x, already installed) was not tried beyond this, because `rope`
worked cleanly on both the Tier-1 and Tier-2 cases above with no rough
edges - `libcst` is lower-level (a concrete-syntax-tree codemod toolkit; it
would require hand-writing the scope resolution `rope` already provides, via
its own `ScopeProvider` metadata) and there was no observed gap in `rope`'s
behaviour that would justify reaching for it. If a future rename case does
defeat `rope` - a dynamic attribute rename, a name rebuilt from a string,
something outside static scope analysis - `libcst`'s metadata providers are
the fallback worth trying next, not a second default choice.
