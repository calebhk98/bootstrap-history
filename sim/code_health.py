#!/usr/bin/env python3
"""code_health.py: the maintainability properties this project asks about by
hand every time somebody wants them, made into one reproducible command.

    python3 sim/code_health.py                 everything, human-readable
    python3 sim/code_health.py --names          just the naming-sweep counts
    python3 sim/code_health.py --duplication    just the duplicated-code report
    python3 sim/code_health.py --complexity     just complexity/size (via radon)
    python3 sim/code_health.py --misc           imports, parameter lists, getattr reads
    python3 sim/code_health.py --json           any of the above, as JSON
    python3 sim/code_health.py record baseline.json   write today's numbers
    python3 sim/code_health.py check baseline.json    diff today against that file

READ-ONLY BY DEFAULT. This file never edits a file under `sim/`, `data/` or
anywhere else in the repository. `record` writes to the path you name, which
you would normally keep outside the checkout or in an untracked scratch
file, exactly the way `sim/perf_fingerprint.py record baseline.json` does -
this file's `record`/`check` verbs are deliberately the same shape as that
one, so a burndown is tracked the same way a fingerprint is, rather than
inventing a third convention.

WHAT THIS COMPOSES WITH, RATHER THAN REBUILDS:

  * `sim/prove_rename_safe.py` - proves a *specific* rename changed nothing
    but names, by bytecode comparison. This file does not attempt that; it
    finds candidates (which names are short, which are Tier 1 - i.e. which
    ones `prove_rename_safe.py` can actually certify) and leaves the proving
    to that tool.
  * `ruff` (`sim/tests/test_static_checks.py`, `ruff.toml`) - already runs
    pyflakes' F-rules as a suite topic, for F821 specifically. This file
    shells out to the same `ruff` binary for two more F-series checks
    (F401 unused imports) and one pycodestyle check (E402, imports not at
    the top) it does not already run, rather than re-implementing an import
    graph by hand. If ruff is not installed, those two checks are skipped
    and say so, exactly like `test_static_checks.py` does - a tool nobody
    has must not make a clean checkout look broken.
  * `radon` - already used throughout this project for cyclomatic
    complexity (CLAUDE.md section 5). This file imports `radon.complexity`
    and `radon.raw` directly rather than reimplementing a complexity
    metric or a line counter.
  * `docs/architecture/NAMING_PLAN.md` - CLAUDE.md section 7 quotes eight
    numbers from that plan's own scanner and says outright that the
    scanner "is not part of this repo; it is a throwaway analysis script,
    not a shipped tool", so those eight numbers are measured but
    unverifiable. THE SINGLE MOST VALUABLE THING THIS FILE DOES is commit
    that scanner - three ways of counting a short identifier, matching the
    plan's own three methods (see `--names` below), each labelled with
    which reference figure it is meant to reproduce and, honestly, whether
    it does. It frequently does not: see that section's own docstring for
    why, and run it yourself rather than trust a number quoted here, since
    per CLAUDE.md section 8 a number in prose is only as good as the
    command sitting next to it.

DETERMINISM. Every detector below is a pure function of the source text on
disk - no wall-clock timestamps, no `id()`-keyed caches (CLAUDE.md section
6 records what that habit already cost this project once), no `set()`
iteration order leaking into JSON without a `sorted()` first. Two ordinary
runs against an unchanged tree must produce byte-identical output; if they
do not, that is a bug in this file, not noise to route around.
"""
import argparse
import ast
import collections
import difflib
import hashlib
import json
import os
import subprocess
import sys
import symtable

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ============================================================================
# SHARED: finding source files, portably (see sim/tests/test_suite_portability.py
# for why this matters - a hardcoded "rome" or an assumption about cwd breaks
# a fresh clone under any other name, in any other directory).
# ============================================================================


def python_files(base=None, exclude_dirs=("__pycache__",)):
    """Every .py file under `base` (default: sim/), relative to ROOT, sorted.

    Sorted so every detector below sees files in the same order on every
    run, on every machine - `os.walk`'s own order is filesystem-dependent
    and is exactly the kind of thing that would make this file's own output
    nondeterministic if left alone.
    """
    base = base if base is not None else os.path.join(ROOT, "sim")
    out = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(dirname for dirname in dirnames if dirname not in exclude_dirs)
        for filename in filenames:
            if filename.endswith(".py"):
                out.append(os.path.relpath(os.path.join(dirpath, filename), ROOT))
    return sorted(out)


def _read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


def _parse(path):
    """Return (source, ast_tree) for `path`, or (source, None) if it does not
    parse. A syntax error in one file must not take the whole scan down."""
    source = _read(path)
    try:
        return source, ast.parse(source, filename=path)
    except SyntaxError:
        return source, None


# ============================================================================
# SECTION 1: NAMES - the naming-sweep scanner CLAUDE.md section 7 says does
# not exist as a committed tool. Three counting methods, matching the three
# CLAUDE.md itself names: occurrences, binding sites, name-per-scope.
# ============================================================================

# CLAUDE.md section 7's own exemptions: "i" as a loop index, and "x"/"y" as
# coordinates. The loop-index exemption is checked by ROLE (was this
# particular binding a for-loop target, not just any binding named "i"). The
# coordinate exemption cannot be checked semantically - "is this line doing
# geometry" is not an AST property - so it is approximated the only concrete
# way NAMING_PLAN.md's own audit found a coordinate use would look: "x" and
# "y" bound together, as a pair, in the same assignment or the same
# for-target (`x, y = ...` or `for x, y in ...`). NAMING_PLAN.md A.2 already
# checked and found zero real coordinate uses of x/y in this codebase today,
# so this exemption is expected to fire zero or near-zero times - it is
# implemented for when it stops being true, not because it currently matters.


def _short(name):
    return name != "_" and len(name) <= 2


class _NameOccurrence(object):
    __slots__ = ("name", "role", "tier", "lineno", "exempt")

    def __init__(self, name, role, tier, lineno, exempt):
        self.name = name
        self.role = role
        self.tier = tier
        self.lineno = lineno
        self.exempt = exempt


class _ScopeVisitor(ast.NodeVisitor):
    """Walk one module, recording every short (<=2 char, not "_") binding
    site with its ROLE (assign / for-target / with-as / except-as /
    comprehension-target / lambda-param / function-param) and its TIER.

    TIER FOLLOWS docs/architecture/NAMING_PLAN.md A.4 exactly:

      Tier 1 (mechanically safe - prove_rename_safe.py can certify it):
        a comprehension target (comprehensions are always their own scope);
        a function-local assign/for-target/with-as/except-as (the direct
        enclosing scope is a function or lambda body, not the module or a
        class body); a lambda parameter.

      Tier 2 (needs a caller check - a keyword-argument call site, or a
      global read from elsewhere in the module):
        a NAMED function's own parameter (def, not lambda), at any nesting
        depth, because prove_rename_safe.py's own documented hole is
        exactly this: a caller passing it by keyword breaks invisibly;
        a module- or class-level assign/for-target/with-as/except-as (the
        direct enclosing scope is the module or a class body, which compile
        to STORE_NAME rather than STORE_FAST - a real global, not a local);
        a module-level `def`/`class` name.

    Only the DIRECT enclosing scope decides Tier for an assign/for-target/
    with-as/except-as site - a module-level statement is Tier 2 even if the
    module also contains functions elsewhere; a statement inside a function
    is Tier 1 even if that function is itself defined inside a class body.
    """

    def __init__(self):
        self.occurrences = []
        self._scope_stack = ["module"]

    def _record(self, name, role, lineno, exempt=False):
        if not _short(name):
            return
        fast_scope = self._scope_stack[-1] in ("function", "lambda", "comprehension")
        if role == "function-param":
            tier = 2
        elif role == "lambda-param":
            tier = 1
        elif role == "def-or-class-name":
            tier = 2
        else:
            tier = 1 if fast_scope else 2
        self.occurrences.append(_NameOccurrence(name, role, tier, lineno, exempt))

    # --- scopes that push a frame -----------------------------------------

    def visit_FunctionDef(self, node):
        self._visit_def(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_def(node)

    def _visit_def(self, node):
        # The def's OWN name lives in whatever scope encloses it (module- or
        # class-level almost always in this codebase), never in the scope
        # it opens.
        self._record(node.name, "def-or-class-name", node.lineno)
        for arg in _all_args(node.args):
            self._record(arg.arg, "function-param", arg.lineno)
        for default in (list(node.args.defaults)
                        + [given for given in node.args.kw_defaults if given]):
            self.visit(default)
        for decorator in node.decorator_list:
            self.visit(decorator)
        if node.returns:
            self.visit(node.returns)
        self._scope_stack.append("function")
        for statement in node.body:
            self.visit(statement)
        self._scope_stack.pop()

    def visit_Lambda(self, node):
        for arg in _all_args(node.args):
            self._record(arg.arg, "lambda-param", node.lineno)
        for default in (list(node.args.defaults)
                        + [given for given in node.args.kw_defaults if given]):
            self.visit(default)
        self._scope_stack.append("lambda")
        self.visit(node.body)
        self._scope_stack.pop()

    def visit_ClassDef(self, node):
        self._record(node.name, "def-or-class-name", node.lineno)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        for decorator in node.decorator_list:
            self.visit(decorator)
        self._scope_stack.append("class")
        for statement in node.body:
            self.visit(statement)
        self._scope_stack.pop()

    def _visit_comprehension(self, node):
        self._scope_stack.append("comprehension")
        # `iter` of the FIRST generator is evaluated in the ENCLOSING scope in
        # real Python semantics, but that distinction does not change any
        # Tier decision here (an outer-scope read is not a Store site at
        # all), so it is not worth special-casing; every generator's `iter`
        # and every filter `if` is walked inside the comprehension's own
        # scope frame for simplicity.
        for generator in node.generators:
            self._visit_target(generator.target, "comprehension-target")
            self.visit(generator.iter)
            for condition in generator.ifs:
                self.visit(condition)
        if hasattr(node, "elt"):
            self.visit(node.elt)
        else:  # DictComp
            self.visit(node.key)
            self.visit(node.value)
        self._scope_stack.pop()

    def visit_ListComp(self, node):
        self._visit_comprehension(node)

    def visit_SetComp(self, node):
        self._visit_comprehension(node)

    def visit_GeneratorExp(self, node):
        self._visit_comprehension(node)

    def visit_DictComp(self, node):
        self._visit_comprehension(node)

    # --- binding sites that do not open a scope -----------------------------

    def _visit_target(self, target, role):
        """A Store-context target: a plain Name, or a Tuple/List of them
        (`a, b = ...`), possibly nested. Also implements both CLAUDE.md
        section 7 exemptions: "i" as a loop index (any for-target or
        comprehension-target literally named "i" - the ROLE is what makes
        it a loop index, not merely the spelling), and the x/y-together
        coordinate exemption (a Name is exempt only when its immediate
        sibling in the SAME tuple/list target is the other of "x"/"y")."""
        if isinstance(target, ast.Name):
            is_loop_index_i = (target.id == "i"
                               and role in ("for-target", "comprehension-target"))
            self._record(target.id, role, target.lineno, exempt=is_loop_index_i)
        elif isinstance(target, (ast.Tuple, ast.List)):
            names_here = [element.id for element in target.elts
                          if isinstance(element, ast.Name)]
            paired_xy = "x" in names_here and "y" in names_here
            for element in target.elts:
                if isinstance(element, ast.Name) and element.id in ("x", "y") and paired_xy:
                    self._record(element.id, role, element.lineno, exempt=True)
                else:
                    self._visit_target(element, role)
        elif isinstance(target, ast.Starred):
            self._visit_target(target.value, role)
        # Attribute/Subscript targets (`self.k = ...`, `d[k] = ...`) bind no
        # new name at all - the thing on the left is a read of `self`/`d`,
        # not a Store of a short identifier - so nothing to record there.

    def visit_Assign(self, node):
        for target in node.targets:
            self._visit_target(target, "assign")
        self.visit(node.value)

    def visit_AugAssign(self, node):
        self._visit_target(node.target, "assign")
        self.visit(node.value)

    def visit_AnnAssign(self, node):
        self._visit_target(node.target, "assign")
        if node.value:
            self.visit(node.value)

    def visit_NamedExpr(self, node):  # the walrus operator, `k := ...`
        self._visit_target(node.target, "assign")
        self.visit(node.value)

    def visit_For(self, node):
        self._visit_target(node.target, "for-target")
        self.visit(node.iter)
        for statement in node.body:
            self.visit(statement)
        for statement in node.orelse:
            self.visit(statement)

    def visit_AsyncFor(self, node):
        self.visit_For(node)

    def visit_With(self, node):
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None:
                self._visit_target(item.optional_vars, "with-as")
        for statement in node.body:
            self.visit(statement)

    def visit_AsyncWith(self, node):
        self.visit_With(node)

    def visit_ExceptHandler(self, node):
        if node.type:
            self.visit(node.type)
        if node.name:
            # A bare string, not a Name node - `except X as e:` compiles the
            # target as its own kind of Store, never visible as ast.Name.
            self._record(node.name, "except-as", node.lineno)
        for statement in node.body:
            self.visit(statement)


def _all_args(arguments):
    """Every ast.arg across a function's whole signature, in a stable order:
    positional-only, positional-or-keyword, *args, keyword-only, **kwargs."""
    out = list(arguments.posonlyargs) + list(arguments.args)
    if arguments.vararg:
        out.append(arguments.vararg)
    out += list(arguments.kwonlyargs)
    if arguments.kwarg:
        out.append(arguments.kwarg)
    return out


def scan_occurrences(files):
    """Method 1: OCCURRENCES - "what a rename tool must actually touch"
    (CLAUDE.md section 7). Every Store-context binding site of a short
    identifier, counting a name rebound five times in one function as five,
    because a mechanical renamer has to touch all five. This is the same
    method docs/architecture/NAMING_PLAN.md's own re-scan describes (its
    "This plan re-scans sim/..." paragraph): every Name(Store), every
    for-target, with-as, except-as, and every function/lambda parameter.
    NOTE ON EXEMPTIONS. CLAUDE.md section 7's reference figures (4,972
    occurrences, the 72.4% Tier-1 share) were measured INCLUDING every use
    of "i" and "x"/"y" - docs/architecture/NAMING_PLAN.md's own per-name
    table counts "i" among the 4,972 and calls it "CONSISTENT - leave it",
    it does not remove it. So `total`/`per_name`/`tier1`/`tier2` below
    include exempt occurrences too, to stay comparable to that figure. A
    SEPARATE, smaller `flagged_total`/`flagged_per_name` excludes them -
    that is the "still worth renaming" figure, distinct from "what a rename
    tool would have to touch if it touched everything".
    """
    per_file = {}
    per_name = collections.Counter()
    per_name_files = collections.defaultdict(set)
    flagged_per_name = collections.Counter()
    tier_counts = collections.Counter()
    exempt_count = 0
    total = 0
    files_with_hits = 0

    for path in files:
        _, tree = _parse(path)
        if tree is None:
            continue
        visitor = _ScopeVisitor()
        visitor.visit(tree)
        if not visitor.occurrences:
            continue
        files_with_hits += 1
        file_names = collections.Counter()
        for occurrence in visitor.occurrences:
            total += 1
            per_name[occurrence.name] += 1
            per_name_files[occurrence.name].add(path)
            file_names[occurrence.name] += 1
            tier_counts[occurrence.tier] += 1
            if occurrence.exempt:
                exempt_count += 1
            else:
                flagged_per_name[occurrence.name] += 1
        per_file[path] = dict(sorted(file_names.items()))

    tier1 = tier_counts.get(1, 0)
    tier2 = tier_counts.get(2, 0)
    return {
        "total": total,
        "flagged_total": total - exempt_count,
        "distinct_names": len(per_name),
        "files_with_hits": files_with_hits,
        "files_scanned": len(files),
        "exempted": exempt_count,
        "flagged_per_name": {name: count for name, count in flagged_per_name.most_common()},
        "tier1": tier1,
        "tier2": tier2,
        "tier1_share_pct": round(100.0 * tier1 / total, 1) if total else 0.0,
        "per_name": {name: count for name, count in per_name.most_common()},
        "per_name_file_count": {name: len(per_name_files[name])
                                for name, _ in per_name.most_common()},
        "per_file": dict(sorted(per_file.items(), key=lambda item: (-sum(item[1].values()), item[0]))),
    }


def scan_name_per_scope(files):
    """Method 3: NAME-PER-SCOPE - "what a reader meets" (CLAUDE.md section
    7). One binding per (name, scope) pair, via Python's own `symtable`
    module, rather than one per rebinding - a variable reassigned five times
    in a loop counts once. This is docs/architecture/NAMING_PLAN.md's own
    cross-check method (its "second cross-check with Python's own symtable
    module" paragraph), including the same artifact it flags: a
    comprehension's own implicit first parameter is named ".0" by CPython
    (2 characters, so it clears the length filter although no source line
    ever spells it), which is why this returns BOTH a total that includes
    those and one that discards them - CLAUDE.md quotes the including
    figure (3,759) as "name-per-scope".
    """
    per_name = collections.Counter()
    per_name_no_artifacts = collections.Counter()
    total = total_no_artifacts = 0
    files_with_hits = 0

    for path in files:
        source = _read(path)
        try:
            top = symtable.symtable(source, path, "exec")
        except SyntaxError:
            continue
        hit_here = False
        for table in _walk_symtable(top):
            for symbol in table.get_symbols():
                name = symbol.get_name()
                if not _short(name):
                    continue
                if not (symbol.is_parameter() or symbol.is_assigned()):
                    continue
                total += 1
                per_name[name] += 1
                hit_here = True
                if not name.startswith("."):
                    total_no_artifacts += 1
                    per_name_no_artifacts[name] += 1
        if hit_here:
            files_with_hits += 1

    return {
        "total_including_comprehension_artifacts": total,
        "total_excluding_comprehension_artifacts": total_no_artifacts,
        "distinct_names": len(per_name),
        "files_with_hits": files_with_hits,
        "files_scanned": len(files),
        "per_name": {name: count for name, count in per_name.most_common()},
        "per_name_excluding_artifacts": {name: count for name, count
                                         in per_name_no_artifacts.most_common()},
    }


def _walk_symtable(table):
    yield table
    for child in table.get_children():
        yield from _walk_symtable(child)


# The figures CLAUDE.md section 7 itself quotes, so a caller can see the
# comparison without re-reading the prose. Every one of these is labelled in
# CLAUDE.md as either reproducible by a command (none exist for these) or
# "measured but unverifiable" - see docs/architecture/NAMING_PLAN.md for
# where each came from. This dict exists so `--names` can report, for each
# one, whether THIS scan's own number matches it - it is not this file
# asserting the historical figures are correct.
CLAUDE_MD_REFERENCE = {
    "occurrences_total": 4972,
    "binding_sites_total": 3813,
    "name_per_scope_total": 3759,
    "distinct_names_range": [176, 332],
    "files_with_hits_of_83": 72,
    "tier1_share_pct": 72.4,
    "k_occurrences": 568,
    "k_files": 53,
}


def names_report(files):
    occurrences = scan_occurrences(files)
    per_scope = scan_name_per_scope(files)

    k_today = occurrences["per_name"].get("k", 0)
    k_files_today = occurrences["per_name_file_count"].get("k", 0)

    reproduces = {
        "occurrences_total": occurrences["total"] == CLAUDE_MD_REFERENCE["occurrences_total"],
        "name_per_scope_total": (per_scope["total_including_comprehension_artifacts"]
                                  == CLAUDE_MD_REFERENCE["name_per_scope_total"]),
        "tier1_share_pct": abs(occurrences["tier1_share_pct"]
                               - CLAUDE_MD_REFERENCE["tier1_share_pct"]) < 0.05,
        "k_occurrences": k_today == CLAUDE_MD_REFERENCE["k_occurrences"],
        "k_files": k_files_today == CLAUDE_MD_REFERENCE["k_files"],
        "files_with_hits_of_83": (occurrences["files_scanned"] == 83
                                   and occurrences["files_with_hits"]
                                       == CLAUDE_MD_REFERENCE["files_with_hits_of_83"]),
        # "binding sites" (3,813) has no reproducible definition to check
        # against: docs/architecture/NAMING_PLAN.md's own investigation of
        # the gap between its re-scan (4,972) and this number concluded the
        # ORIGINAL scan's exact grammar is lost, not merely uncommitted -
        # unlike the other two counts, there is no described method this
        # file can re-implement and call the same thing. Reported as None,
        # meaning "not verifiable, not merely not matching", rather than
        # quietly guessing at a definition and reporting a false match or
        # mismatch against it.
        "binding_sites_total": None,
    }

    return {
        "occurrences": occurrences,
        "name_per_scope": per_scope,
        "claude_md_reference": CLAUDE_MD_REFERENCE,
        "reproduces_claude_md": reproduces,
        "files_scanned": occurrences["files_scanned"],
    }


def print_names_report(report, limit=15):
    occ = report["occurrences"]
    scope = report["name_per_scope"]
    ref = report["claude_md_reference"]
    rep = report["reproduces_claude_md"]

    print("NAMES  (identifiers <= 2 characters, excluding \"_\")")
    print("  scanned %d files under sim/" % report["files_scanned"])
    print()
    print("  method 1, occurrences (what a rename tool must touch):")
    print("    today: %d occurrences, %d distinct names, %d/%d files with >=1 hit"
          % (occ["total"], occ["distinct_names"], occ["files_with_hits"], occ["files_scanned"]))
    print("    CLAUDE.md quotes: %d occurrences, %d-%d distinct names, %d files (of 83)"
          % (ref["occurrences_total"], ref["distinct_names_range"][0],
             ref["distinct_names_range"][1], ref["files_with_hits_of_83"]))
    print("    reproduces CLAUDE.md's occurrence total: %s"
          % ("YES" if rep["occurrences_total"] else "NO"))
    print()
    print("  Tier 1 (mechanically safe, see prove_rename_safe.py): %d (%.1f%%)"
          % (occ["tier1"], occ["tier1_share_pct"]))
    print("  Tier 2 (parameters / module- or class-level - needs a caller check): %d"
          % occ["tier2"])
    print("    CLAUDE.md quotes Tier-1 share: %.1f%% -- reproduces: %s"
          % (ref["tier1_share_pct"], "YES" if rep["tier1_share_pct"] else "NO"))
    if occ["exempted"]:
        print("  (of which %d are exempt per CLAUDE.md section 7: \"i\" as a loop "
              "index / \"x\"/\"y\" bound together as a coordinate pair - "
              "%d occurrence(s) remain flagged)"
              % (occ["exempted"], occ["flagged_total"]))
    print()
    print("  method 2, binding sites (CLAUDE.md's own %d): NOT independently "
          "reproducible - see docs/architecture/NAMING_PLAN.md's own account of "
          "why the original scan's method is lost, not merely uncommitted."
          % ref["binding_sites_total"])
    print()
    print("  method 3, name-per-scope (what a reader meets, via symtable):")
    print("    today: %d (including the \".0\" comprehension-scope artifact), "
          "%d (excluding it)"
          % (scope["total_including_comprehension_artifacts"],
             scope["total_excluding_comprehension_artifacts"]))
    print("    CLAUDE.md quotes: %d -- reproduces: %s"
          % (ref["name_per_scope_total"], "YES" if rep["name_per_scope_total"] else "NO"))
    print()
    print("  'k' today: %d occurrences across %d files "
          "(CLAUDE.md quotes %d across %d files -- reproduces: %s / %s)"
          % (occ["per_name"].get("k", 0), occ["per_name_file_count"].get("k", 0),
             ref["k_occurrences"], ref["k_files"],
             "YES" if rep["k_occurrences"] else "NO",
             "YES" if rep["k_files"] else "NO"))
    print()
    print("  top names by occurrence:")
    for name, count in list(occ["per_name"].items())[:limit]:
        print("    %-6s %5d  (%d files)" % (name, count, occ["per_name_file_count"][name]))
    print()
    print("  top files by occurrence count:")
    for path, names in list(occ["per_file"].items())[:limit]:
        print("    %5d  %s" % (sum(names.values()), path))


# ============================================================================
# SECTION 2: DUPLICATION - near-identical blocks that have started to
# diverge. The stakeholder's own motivating example: "we recently fixed 1
# place that had 8 different call sites doing the same thing... 3 versions"
# - so the useful unit here is a CLUSTER of related blocks and how many
# distinct shapes it has split into, not a single pairwise diff.
# ============================================================================

# Fields every ast node carries that are about SOURCE POSITION or SYNTACTIC
# CONTEXT rather than what the code DOES - stripped before normalising, the
# same spirit as prove_rename_safe.py blanking a slot index rather than a
# variable's role.
_POSITION_FIELDS = frozenset(
    {"lineno", "col_offset", "end_lineno", "end_col_offset", "ctx", "type_comment"})

# Where a list-of-statements body can be found. Duplication is looked for
# inside each of these independently - a run of statements at the top of a
# for-loop, a whole function body, the arm of an if - rather than only at
# one granularity, because the known case this must find (the pre-extraction
# hazard-window loop - see the test module and this file's own docstring)
# is a handful of statements INSIDE a larger loop that otherwise differs.
_BODY_FIELDS = ("body", "orelse", "finalbody")

# A window of this many consecutive statements is the unit compared.
# Chosen, and verified against a known case, rather than guessed: the
# hazard-window duplicate that existed before sim/engine/hazard_window.py
# was extracted (see sim/tests/test_code_health.py and this module's
# docstring) is exactly 5 statements, and a window of 5 finds it at the
# pre-extraction commit with no tuning. Smaller windows found the same
# location too, buried in noise from tiny, uninteresting matches (a lone
# `if not x: continue` matches constantly); 5 was the smallest window that
# stayed quiet on trivial code while still catching the real case.
DUPLICATE_WINDOW_STATEMENTS = 5

# Windows are taken NON-OVERLAPPING (stride == window) rather than sliding
# by one statement at a time, because a sliding-by-one window over an
# ordinary function produces mostly-overlapping neighbours (window N and
# window N+1 share 4 of 5 statements) - not a second instance of duplicated
# code, but the same statements counted repeatedly, which is also the real
# performance cost: non-overlapping windows cut candidate count and
# near-duplicate bucket sizes by roughly 4x (13,961 -> 3,558 candidates,
# measured on this checkout), with no change in whether the known
# hazard-window case (which starts at the FIRST statement of its
# for-loop body, so a stride-5 window lands on it directly) is still found.
# The trade is real: a duplicate that straddles two non-overlapping windows
# (starts at statement 3 of a 10-statement body, say) can be missed. That is
# an accepted limitation of a fast heuristic instrument, not a soundness
# claim - see this module's docstring.
DUPLICATE_STRIDE = DUPLICATE_WINDOW_STATEMENTS

# A normalised window smaller than this many AST nodes is not reported even
# if it repeats - two one-line `return None` bodies are not the kind of
# drift risk this detector exists for.
DUPLICATE_MIN_NODE_SIZE = 15

# Two candidates in the same coarse "shape bucket" (see _shape_signature)
# whose normalised token-sequence similarity is at least this are reported
# as a diverging pair, even though their exact structure no longer matches.
# Below this point the report was dominated by unrelated five-statement
# blocks which merely shared Python syntax (five assignments, five calls,
# or five guard clauses).  Keep the near-match pass for small edits to a
# copied block, but require almost all of the normalised structure to agree.
NEAR_DUPLICATE_SIMILARITY_THRESHOLD = 0.98

# A shape bucket larger than this is skipped for the O(n^2) near-duplicate
# pass (exact-hash clustering still applies to it) - generic short shapes
# like a single `if`/`return` pair recur constantly and comparing all of
# them pairwise would cost real time for zero interesting findings.
_NEAR_DUPLICATE_BUCKET_CAP = 25

# A hard ceiling on how many pairwise comparisons the near-duplicate pass
# will do in one run, regardless of how many buckets qualify. Without this,
# a codebase with many mid-sized, same-shaped-but-unrelated buckets could
# still add up to an impractical runtime even with every individual bucket
# under the cap above. Exceeding it is reported, not hidden: the summary
# says the near-duplicate pass stopped early, and exact-clone detection
# (the cheap hash-based pass) is entirely unaffected either way.
_NEAR_DUPLICATE_PAIR_BUDGET = 40000


def _normalize(node):
    """Return an alpha-normalised AST without erasing program semantics.

    Names and arguments are numbered by first appearance, so consistently
    renaming locals cannot hide a clone.  Their equality relationships are
    retained, however: ``left + left`` no longer matches ``left + right``.
    Literal values are retained too, because five unrelated declarations
    are not duplicate logic merely because all five contain strings and
    floats.  Attribute and method names continue to be preserved.
    """
    names = {}
    arguments = {}

    def normalize(value):
        if isinstance(value, ast.Name):
            return ("NAME", names.setdefault(value.id, len(names)))
        if isinstance(value, ast.arg):
            return ("ARG", arguments.setdefault(value.arg, len(arguments)))
        if isinstance(value, ast.Constant):
            return ("CONST", type(value.value).__name__, repr(value.value))
        if isinstance(value, ast.AST):
            fields = []
            for field, child in ast.iter_fields(value):
                if field not in _POSITION_FIELDS:
                    fields.append((field, normalize(child)))
            return (type(value).__name__, tuple(fields))
        if isinstance(value, list):
            return tuple(normalize(item) for item in value)
        return value

    return normalize(node)


def _node_size(normalized):
    if isinstance(normalized, tuple):
        return 1 + sum(_node_size(item) for item in normalized)
    return 0


def _flatten_tokens(normalized, out):
    """A normalised subtree, flattened into a pre-order list of small string
    tokens (one per AST node type, plus one for each NAME/ARG/CONST leaf) -
    used for near-duplicate comparison INSTEAD OF a `repr()` string.

    A node's `repr()` carries a lot of Python tuple/string punctuation that
    has nothing to do with the program's structure and everything to do
    with how this file happens to represent it; `difflib.SequenceMatcher`
    over that punctuation-heavy text costs real time (measured on this
    checkout: tens of seconds for a few thousand large-block comparisons)
    for no better an answer than comparing the much shorter token sequence
    directly.
    """
    if (isinstance(normalized, tuple) and len(normalized) in (1, 2)
            and isinstance(normalized[0], str)
            and (len(normalized) == 1 or not isinstance(normalized[1], tuple)
                 or all(isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str)
                        for item in normalized[1]))):
        # A single AST node: ("TypeName",) for NAME/ARG, ("CONST", "str") for
        # a constant, or ("TypeName", ((field, value), (field, value), ...))
        # for everything else. Distinguished from a plain tuple-of-siblings
        # (whose own first element is itself a node-tuple, never a bare
        # string) by shape alone - see the docstring above.
        out.append(normalized[0])
        rest = normalized[1] if len(normalized) > 1 else ()
        if isinstance(rest, tuple):
            for field_name, value in rest:
                _flatten_tokens(value, out)
        else:
            out.append(str(rest))
    elif isinstance(normalized, tuple):
        for item in normalized:
            _flatten_tokens(item, out)
    else:
        out.append(repr(normalized))
    return out


def _shape_signature(window):
    """A coarse fingerprint used only to BUCKET candidates before the
    expensive near-duplicate comparison: the statement TYPES in the window,
    in order, nothing else. Two windows with the same signature are
    plausibly related; two with different signatures are not compared at
    all, which is what keeps the near-duplicate pass affordable."""
    return tuple(type(statement).__name__ for statement in window)


def _is_boilerplate_window(stmts):
    """True for a window that is entirely import statements (and/or a bare
    string constant - a module or function docstring). Every file in this
    codebase opens with some mix of these, so they cluster as "duplicates"
    of each other constantly and mean nothing: two files both starting with
    a docstring, then `import os`, then `import sys`, then `from x import
    (...)` are not the kind of drift risk this detector exists to find.
    Measured:
    without this filter, the highest-ranked clusters on this checkout were
    entirely import preambles: filtering them out is what makes the report
    about the codebase's actual logic rather than its import style."""
    # Consecutive annotations are a schema, not executable copies.  The
    # field names and types are the information; replacing them with a loop
    # or factory would make dataclasses and TypedDicts harder to inspect.
    if all(isinstance(statement, ast.AnnAssign) for statement in stmts):
        return True
    # Comments are not AST statements, so the first executable test setup
    # can otherwise be grouped with the module docstring and import as one
    # enormous-looking "clone".  A window containing the module preamble is
    # not five copied statements of logic; the next non-preamble window will
    # still examine that setup normally.
    first = stmts[0]
    if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
            and any(isinstance(statement, (ast.Import, ast.ImportFrom))
                    for statement in stmts[1:])):
        return True
    for statement in stmts:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            continue
        if (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)):
            continue
        return False
    return True


def _iter_bodies(tree):
    for node in ast.walk(tree):
        for field in _BODY_FIELDS:
            body = getattr(node, field, None)
            if isinstance(body, list) and body and isinstance(body[0], ast.stmt):
                yield body


class _Candidate(object):
    __slots__ = ("path", "lineno", "end_lineno", "size", "tokens", "norm_hash", "shape")

    def __init__(self, path, lineno, end_lineno, size, tokens, norm_hash, shape):
        self.path = path
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.size = size
        self.tokens = tokens          # tuple of str - see _flatten_tokens
        self.norm_hash = norm_hash
        self.shape = shape


def _collect_candidates(files, window=DUPLICATE_WINDOW_STATEMENTS,
                         stride=DUPLICATE_STRIDE, min_size=DUPLICATE_MIN_NODE_SIZE):
    candidates = []
    for path in files:
        _, tree = _parse(path)
        if tree is None:
            continue
        for body in _iter_bodies(tree):
            if len(body) < window:
                continue
            for start in range(0, len(body) - window + 1, stride):
                stmts = body[start:start + window]
                if _is_boilerplate_window(stmts):
                    continue
                normalized = _normalize(stmts)
                size = _node_size(normalized)
                if size < min_size:
                    continue
                tokens = tuple(_flatten_tokens(normalized, []))
                norm_hash = hashlib.sha256("\x1f".join(tokens).encode("utf-8")).hexdigest()
                end_lineno = getattr(stmts[-1], "end_lineno", stmts[-1].lineno)
                candidates.append(_Candidate(
                    path, stmts[0].lineno, end_lineno, size, tokens, norm_hash,
                    _shape_signature(stmts)))
    return candidates


class _UnionFind(object):
    def __init__(self, keys):
        self._parent = {key: key for key in keys}

    def find(self, key):
        root = key
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[key] != root:
            self._parent[key], key = root, self._parent[key]
        return root

    def union(self, key_a, key_b):
        root_a, root_b = self.find(key_a), self.find(key_b)
        if root_a != root_b:
            self._parent[root_b] = root_a


def _cluster_candidates(candidates):
    """Group candidates into connected components: two candidates are in the
    same component when they are an EXACT structural match, or a NEAR match
    (same coarse shape, high token-sequence similarity of the normalised
    form). Returns (clusters, near_duplicate_budget_exhausted).

    Every pairwise ratio the near-duplicate pass computes is cached and
    reused when a cluster's own "how similar are its non-identical members"
    figure is built afterwards, rather than recomputed - see
    `_flatten_tokens`'s docstring for why the comparison itself is cheap
    only once, not for why recomputing it twice would be free.

    Clusters with >= 2 members are returned, each annotated with how many
    distinct exact shapes ("versions") its members have collapsed into -
    the direct answer to "did 1 place become 3 versions".
    """
    if not candidates:
        return [], False
    keys = list(range(len(candidates)))
    union_find = _UnionFind(keys)
    ratio_cache = {}

    by_hash = collections.defaultdict(list)
    for index, candidate in enumerate(candidates):
        by_hash[candidate.norm_hash].append(index)
    for indices in by_hash.values():
        for other in indices[1:]:
            union_find.union(indices[0], other)

    by_shape = collections.defaultdict(list)
    for index, candidate in enumerate(candidates):
        by_shape[candidate.shape].append(index)

    pairs_spent = 0
    budget_exhausted = False
    for indices in by_shape.values():
        if len(indices) < 2 or len(indices) > _NEAR_DUPLICATE_BUCKET_CAP:
            continue
        if budget_exhausted:
            break
        for i in range(len(indices)):
            if budget_exhausted:
                break
            for other_position in range(i + 1, len(indices)):
                if pairs_spent >= _NEAR_DUPLICATE_PAIR_BUDGET:
                    budget_exhausted = True
                    break
                candidate_a, candidate_b = candidates[indices[i]], candidates[indices[other_position]]
                if candidate_a.norm_hash == candidate_b.norm_hash:
                    continue  # already unioned via the exact pass
                # A length-ratio prefilter: two blocks whose token counts
                # differ by more than this cannot reach the similarity
                # threshold under SequenceMatcher's own definition (ratio is
                # bounded by 2*min/(len_a+len_b)), so skip the comparison
                # entirely rather than pay for a SequenceMatcher that could
                # only ever answer "no".
                shorter, longer = sorted((len(candidate_a.tokens), len(candidate_b.tokens)))
                if longer and (2.0 * shorter / (shorter + longer)) < NEAR_DUPLICATE_SIMILARITY_THRESHOLD:
                    continue
                pairs_spent += 1
                matcher = difflib.SequenceMatcher(None, candidate_a.tokens, candidate_b.tokens, autojunk=False)
                if matcher.quick_ratio() < NEAR_DUPLICATE_SIMILARITY_THRESHOLD:
                    continue
                ratio = matcher.ratio()
                if ratio >= NEAR_DUPLICATE_SIMILARITY_THRESHOLD:
                    union_find.union(indices[i], indices[other_position])
                    ratio_cache[(indices[i], indices[other_position])] = ratio

    components = collections.defaultdict(list)
    for index in keys:
        components[union_find.find(index)].append(index)

    clusters = []
    for indices in components.values():
        if len(indices) < 2:
            continue
        members = [candidates[i] for i in indices]
        distinct_hashes = {member.norm_hash for member in members}
        # A "diverged" measure: the mean pairwise similarity among members
        # that do NOT share an exact hash, drawn from the cache above - every
        # pair inside one cluster necessarily shares one shape bucket (an
        # exact-hash union never crosses shapes, since equal normalised
        # structure implies equal statement-type shape; a near-duplicate
        # union never crosses shapes by construction), so a pair with
        # differing hashes was, if it was ever compared at all, compared
        # inside THIS pass and its ratio is already in the cache. 1.0 (no
        # divergence measured) when every member is an exact structural
        # clone of every other, or when the pair was never compared because
        # a bucket exceeded the cap or the run hit its budget.
        cross_version_ratios = []
        for i in range(len(indices)):
            for other_position in range(i + 1, len(indices)):
                left, right = sorted((indices[i], indices[other_position]))
                if candidates[left].norm_hash != candidates[right].norm_hash:
                    cached = ratio_cache.get((left, right))
                    if cached is not None:
                        cross_version_ratios.append(cached)
        mean_similarity = (sum(cross_version_ratios) / len(cross_version_ratios)
                           if cross_version_ratios else 1.0)
        clusters.append({
            "members": sorted(
                ({"path": member.path, "line": member.lineno, "end_line": member.end_lineno,
                  "size": member.size, "version_hash": member.norm_hash[:12]}
                 for member in members),
                key=lambda entry: (entry["path"], entry["line"])),
            "member_count": len(members),
            "distinct_versions": len(distinct_hashes),
            "mean_cross_version_similarity": round(mean_similarity, 3),
            "max_member_size": max(member.size for member in members),
        })

    # Ranked by how much a cluster has diverged: the more distinct versions
    # a once-shared shape has split into, the worse the drift risk the
    # stakeholder described - "1 place ... ended up being 3 versions".
    # Ties broken by size (bigger blocks worth fixing first) then by member
    # count, both descending, and finally by the members themselves so the
    # order is fully determined and reproducible run to run.
    clusters.sort(key=lambda cluster: (
        -cluster["distinct_versions"], -cluster["max_member_size"],
        -cluster["member_count"],
        tuple((entry["path"], entry["line"]) for entry in cluster["members"])))
    return clusters, budget_exhausted


def duplication_report(files):
    candidates = _collect_candidates(files)
    clusters, budget_exhausted = _cluster_candidates(candidates)
    exact_only = [cluster for cluster in clusters if cluster["distinct_versions"] == 1]
    diverged = [cluster for cluster in clusters if cluster["distinct_versions"] > 1]
    return {
        "window_statements": DUPLICATE_WINDOW_STATEMENTS,
        "stride": DUPLICATE_STRIDE,
        "min_node_size": DUPLICATE_MIN_NODE_SIZE,
        "candidates_scanned": len(candidates),
        "cluster_count": len(clusters),
        "exact_clone_clusters": len(exact_only),
        "diverging_clusters": len(diverged),
        "near_duplicate_budget_exhausted": budget_exhausted,
        "clusters": clusters,
    }


def print_duplication_report(report, limit=10):
    print("DUPLICATION  (non-overlapping window of %d consecutive statements, "
          ">= %d normalised AST nodes)"
          % (report["window_statements"], report["min_node_size"]))
    print("  %d candidate blocks scanned, %d cluster(s) with >= 2 members "
          "(%d exact clones, %d showing divergence into more than one version)"
          % (report["candidates_scanned"], report["cluster_count"],
             report["exact_clone_clusters"], report["diverging_clusters"]))
    if report["near_duplicate_budget_exhausted"]:
        print("  NOTE: the near-duplicate comparison budget (%d pairs) was used up - "
              "exact-clone clusters above are unaffected, but some divergent "
              "clusters may be missing or under-counted." % _NEAR_DUPLICATE_PAIR_BUDGET)
    print()
    print("  top clusters, most-diverged (most distinct versions) first:")
    for cluster in report["clusters"][:limit]:
        print("    %d version(s) across %d site(s), size %d, "
              "mean similarity between versions %.2f"
              % (cluster["distinct_versions"], cluster["member_count"],
                 cluster["max_member_size"], cluster["mean_cross_version_similarity"]))
        for member in cluster["members"]:
            print("        %s:%d-%d" % (member["path"], member["line"], member["end_line"]))


# ============================================================================
# SECTION 3: COMPLEXITY AND SIZE - composed from radon, not reimplemented.
# ============================================================================

COMPLEXITY_THRESHOLD = 15
CODE_LINE_THRESHOLD = 1000     # SLOC: source lines, blank/comment-only excluded
TOTAL_LINE_THRESHOLD = 2000    # LOC: every physical line, including comments


def _radon_available():
    try:
        import radon.complexity  # noqa: F401
        import radon.raw  # noqa: F401
    except ImportError:
        return False
    return True


def complexity_report(files):
    if not _radon_available():
        return {"available": False}

    from radon.complexity import cc_visit
    from radon.raw import analyze
    from radon.visitors import Function as RadonFunction

    over_threshold = []
    files_over_code_lines = []
    files_over_total_lines = []
    complexity_failures = []

    for path in files:
        source = _read(path)
        try:
            raw = analyze(source)
        except Exception as exc:  # radon can choke on the odd file; skip, don't crash
            complexity_failures.append("%s: raw analysis failed: %s" % (path, exc))
            raw = None
        if raw is not None:
            if raw.sloc > CODE_LINE_THRESHOLD:
                files_over_code_lines.append({"path": path, "code_lines": raw.sloc,
                                              "total_lines": raw.loc})
            if raw.loc > TOTAL_LINE_THRESHOLD:
                files_over_total_lines.append({"path": path, "total_lines": raw.loc,
                                               "code_lines": raw.sloc})
        try:
            for item in cc_visit(source, no_assert=True):
                if isinstance(item, RadonFunction) and item.complexity > COMPLEXITY_THRESHOLD:
                    qualified = ("%s.%s" % (item.classname, item.name)
                                if getattr(item, "classname", None) else item.name)
                    over_threshold.append({"path": path, "name": qualified,
                                           "line": item.lineno,
                                           "complexity": item.complexity})
        except Exception as exc:
            complexity_failures.append("%s: complexity analysis failed: %s" % (path, exc))

    over_threshold.sort(key=lambda entry: (-entry["complexity"], entry["path"], entry["line"]))
    files_over_code_lines.sort(key=lambda entry: (-entry["code_lines"], entry["path"]))
    files_over_total_lines.sort(key=lambda entry: (-entry["total_lines"], entry["path"]))

    return {
        "available": True,
        "complexity_threshold": COMPLEXITY_THRESHOLD,
        "code_line_threshold": CODE_LINE_THRESHOLD,
        "total_line_threshold": TOTAL_LINE_THRESHOLD,
        "functions_over_threshold": over_threshold,
        "files_over_code_lines": files_over_code_lines,
        "files_over_total_lines": files_over_total_lines,
        "analysis_failures": complexity_failures,
    }


def print_complexity_report(report, limit=15):
    print("COMPLEXITY AND SIZE  (via radon)")
    if not report["available"]:
        print("  SKIPPED: radon is not installed (python3 -m pip install radon)")
        return
    functions = report["functions_over_threshold"]
    print("  %d function(s) above cyclomatic complexity %d"
          % (len(functions), report["complexity_threshold"]))
    for entry in functions[:limit]:
        print("    %3d  %s:%d  %s" % (entry["complexity"], entry["path"],
                                      entry["line"], entry["name"]))
    print()
    code_files = report["files_over_code_lines"]
    print("  %d file(s) above %d code lines (SLOC - blank/comment lines excluded)"
          % (len(code_files), report["code_line_threshold"]))
    for entry in code_files[:limit]:
        print("    %5d code lines (%5d total)  %s"
              % (entry["code_lines"], entry["total_lines"], entry["path"]))
    print()
    total_files = report["files_over_total_lines"]
    print("  %d file(s) above %d total lines"
          % (len(total_files), report["total_line_threshold"]))
    for entry in total_files[:limit]:
        print("    %5d total lines (%5d code)  %s"
              % (entry["total_lines"], entry["code_lines"], entry["path"]))
    if report["analysis_failures"]:
        print()
        print("  %d file(s) radon could not analyse:" % len(report["analysis_failures"]))
        for line in report["analysis_failures"][:limit]:
            print("    %s" % line)


# ============================================================================
# SECTION 4: MISCELLANEOUS - checks that turned out to have real true
# positives in THIS codebase when measured. What was measured and rejected
# for having none is listed in the module docstring's sibling, the task
# report, and NOT implemented here - a check that always says "clean" earns
# no trust and is not worth the runtime.
# ============================================================================

LONG_PARAMETER_THRESHOLD = 7  # non-self/cls parameters


def _ruff_command():
    """Mirrors sim/tests/test_static_checks.py's own probe exactly, so the
    two files agree about whether ruff is usable rather than reaching two
    different answers about the same interpreter."""
    for command in (["ruff", "--version"], [sys.executable, "-m", "ruff", "--version"]):
        try:
            finished = subprocess.run(command, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            continue
        if finished.returncode == 0:
            return command[:-1]
    return None


def _run_ruff(command, extra_args, paths):
    finished = subprocess.run(
        command + extra_args + [os.path.join(ROOT, path) for path in paths],
        capture_output=True, text=True, timeout=300, cwd=ROOT)
    if finished.returncode not in (0, 1):
        return None, finished.stderr
    return finished.stdout, None


def unused_imports_report(files):
    """F401 via ruff, using this repo's OWN ruff.toml (not --isolated, unlike
    test_static_checks.py's F821 check) - deliberately, because ruff.toml's
    per-file-ignores already excuses sim/simulator.py and
    sim/engine/protocol.py, both documented re-export composition points
    whose "unused" imports are the file doing its job. Running isolated
    would report those as findings and be wrong about it."""
    command = _ruff_command()
    if command is None:
        return {"available": False, "count": 0, "by_file": {}, "note": None}
    stdout, error = _run_ruff(command, ["check", "--select", "F401",
                                        "--output-format", "concise"], files)
    if error is not None:
        return {"available": False, "count": 0, "by_file": {}, "note": "ruff failed: %s" % error}
    by_file = collections.Counter()
    for line in stdout.splitlines():
        if "F401" not in line:
            continue
        path = line.split(":", 1)[0]
        by_file[os.path.relpath(path, ROOT) if os.path.isabs(path) else path] += 1
    return {
        "available": True,
        "count": sum(by_file.values()),
        "by_file": dict(sorted(by_file.items(), key=lambda item: (-item[1], item[0]))),
        "note": ("counts respect ruff.toml's per-file-ignores; a file can still be a "
                 "legitimate, undeclared re-export shim (see solve_prices.py in the "
                 "task report) without being listed there"),
    }


def imports_not_at_top_report(files):
    """E402 via ruff. A late, deliberate, `# noqa: E402`-marked import (this
    repo's own `sys.path.insert(...)` -then-`import` idiom) is already
    excluded by ruff itself honouring the noqa comment, so every finding
    here is an import ruff considers both late AND unexplained."""
    command = _ruff_command()
    if command is None:
        return {"available": False, "count": 0, "by_file": {}}
    stdout, error = _run_ruff(command, ["check", "--select", "E402",
                                        "--output-format", "concise"], files)
    if error is not None:
        return {"available": False, "count": 0, "by_file": {}, "note": "ruff failed: %s" % error}
    by_file = collections.Counter()
    for line in stdout.splitlines():
        if "E402" not in line:
            continue
        path = line.split(":", 1)[0]
        by_file[os.path.relpath(path, ROOT) if os.path.isabs(path) else path] += 1
    return {
        "available": True,
        "count": sum(by_file.values()),
        "by_file": dict(sorted(by_file.items(), key=lambda item: (-item[1], item[0]))),
    }


def long_parameter_list_report(files, threshold=LONG_PARAMETER_THRESHOLD):
    findings = []
    for path in files:
        _, tree = _parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            names = [arg.arg for arg in _all_args(node.args)
                     if arg.arg not in ("self", "cls")]
            if len(names) >= threshold:
                findings.append({"path": path, "line": node.lineno, "name": node.name,
                                 "parameter_count": len(names)})
    findings.sort(key=lambda entry: (-entry["parameter_count"], entry["path"], entry["line"]))
    return {"threshold": threshold, "count": len(findings), "findings": findings}


def lazy_getattr_report(files):
    """`getattr(self, "name", default)` - a lazy-field read where a name's
    absence on `self` is meaningful (typically: the attribute is only ever
    set by some code paths, e.g. a save loaded from before the field
    existed, or a feature only initialised under a flag). Flagged here as a
    genuine problem, not invented: names like "fog" cluster across dozens
    of call sites read this way, which is itself evidence of an attribute
    whose presence isn't guaranteed anywhere central.
    """
    receiver_names = ("self", "s", "sim")

    def _rooted_in_receiver(expr):
        """True for `self`/`s`/`sim`, or an attribute chain rooted in one of
        them (`self.household`, `sim.civ`, ...) - deliberately NOT true for
        an attribute chain rooted in anything else, so this does not flag
        `getattr(some_other_module.thing, "x", default)`, which is not a
        lazy read of the object's OWN field at all."""
        while isinstance(expr, ast.Attribute):
            expr = expr.value
        return isinstance(expr, ast.Name) and expr.id in receiver_names

    findings = []
    for path in files:
        _, tree = _parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "getattr" and len(node.args) >= 3):
                continue
            receiver = node.args[0]
            attribute = node.args[1]
            if not (_rooted_in_receiver(receiver) and isinstance(attribute, ast.Constant)
                    and isinstance(attribute.value, str)):
                continue
            findings.append({"path": path, "line": node.lineno, "attribute": attribute.value})
    findings.sort(key=lambda entry: (entry["attribute"], entry["path"], entry["line"]))
    by_attribute = collections.Counter(entry["attribute"] for entry in findings)
    return {
        "count": len(findings),
        "findings": findings,
        "by_attribute": dict(sorted(by_attribute.items(), key=lambda item: (-item[1], item[0]))),
    }


def misc_report(files):
    return {
        "unused_imports": unused_imports_report(files),
        "imports_not_at_top": imports_not_at_top_report(files),
        "long_parameter_lists": long_parameter_list_report(files),
        "lazy_getattr_reads": lazy_getattr_report(files),
    }


def print_misc_report(report, limit=10):
    print("MISCELLANEOUS")
    unused = report["unused_imports"]
    print("  unused imports (ruff F401):")
    if not unused["available"]:
        print("    SKIPPED: ruff is not installed (python3 -m pip install ruff)"
              if unused.get("note") is None else "    SKIPPED: %s" % unused["note"])
    else:
        print("    %d finding(s)" % unused["count"])
        if unused.get("note"):
            print("    note: %s" % unused["note"])
        for path, count in list(unused["by_file"].items())[:limit]:
            print("      %4d  %s" % (count, path))
    print()
    at_top = report["imports_not_at_top"]
    print("  imports not at the top of the file (ruff E402, noqa already excluded):")
    if not at_top["available"]:
        print("    SKIPPED: ruff is not installed (python3 -m pip install ruff)")
    else:
        print("    %d finding(s)" % at_top["count"])
        for path, count in list(at_top["by_file"].items())[:limit]:
            print("      %4d  %s" % (count, path))
    print()
    params = report["long_parameter_lists"]
    print("  functions with >= %d parameters (excluding self/cls):" % params["threshold"])
    print("    %d finding(s)" % params["count"])
    for entry in params["findings"][:limit]:
        print("      %2d  %s:%d  %s" % (entry["parameter_count"], entry["path"],
                                        entry["line"], entry["name"]))
    print()
    lazy = report["lazy_getattr_reads"]
    print("  getattr(self, \"name\", default) lazy-field reads:")
    print("    %d finding(s), by attribute name:" % lazy["count"])
    for name, count in list(lazy["by_attribute"].items())[:limit]:
        print("      %2d  %s" % (count, name))


# ============================================================================
# ASSEMBLY, CLI, AND THE record/check BASELINE COMPARISON
# (shaped after sim/perf_fingerprint.py's own record/check, deliberately -
# see this file's module docstring for why a third convention was rejected)
# ============================================================================


def full_report(files=None):
    files = files if files is not None else python_files()
    return {
        "files_scanned": len(files),
        "names": names_report(files),
        "duplication": duplication_report(files),
        "complexity": complexity_report(files),
        "misc": misc_report(files),
    }


_SECTION_PRINTERS = {
    "names": lambda report: print_names_report(report["names"]),
    "duplication": lambda report: print_duplication_report(report["duplication"]),
    "complexity": lambda report: print_complexity_report(report["complexity"]),
    "misc": lambda report: print_misc_report(report["misc"]),
}


def print_report(report, sections=None):
    sections = sections or ["names", "duplication", "complexity", "misc"]
    for index, section in enumerate(sections):
        if index:
            print()
            print("-" * 72)
            print()
        _SECTION_PRINTERS[section](report)


# --- a flat "scoreboard" of numbers, for record/check. Mirrors
# perf_fingerprint's own digest-of-state idea, but there is nothing here
# worth hashing away (unlike a full simulation state) - the numbers
# themselves ARE the small, readable summary, so record/check compares them
# directly rather than through a hash.

def _scoreboard(report):
    names = report["names"]["occurrences"]
    scope = report["names"]["name_per_scope"]
    dup = report["duplication"]
    comp = report["complexity"]
    misc = report["misc"]
    board = {
        "files_scanned": report["files_scanned"],
        "names.occurrences_total": names["total"],
        "names.distinct_names": names["distinct_names"],
        "names.tier1": names["tier1"],
        "names.tier2": names["tier2"],
        "names.tier1_share_pct": names["tier1_share_pct"],
        "names.name_per_scope_total": scope["total_including_comprehension_artifacts"],
        "duplication.candidates_scanned": dup["candidates_scanned"],
        "duplication.cluster_count": dup["cluster_count"],
        "duplication.exact_clone_clusters": dup["exact_clone_clusters"],
        "duplication.diverging_clusters": dup["diverging_clusters"],
    }
    if comp["available"]:
        board["complexity.functions_over_threshold"] = len(comp["functions_over_threshold"])
        board["complexity.files_over_code_lines"] = len(comp["files_over_code_lines"])
        board["complexity.files_over_total_lines"] = len(comp["files_over_total_lines"])
    if misc["unused_imports"]["available"]:
        board["misc.unused_imports"] = misc["unused_imports"]["count"]
        board["misc.imports_not_at_top"] = misc["imports_not_at_top"]["count"]
    board["misc.long_parameter_lists"] = misc["long_parameter_lists"]["count"]
    board["misc.lazy_getattr_reads"] = misc["lazy_getattr_reads"]["count"]
    return board


def cmd_record(path):
    report = full_report()
    board = _scoreboard(report)
    with open(path, "w") as handle:
        json.dump(board, handle, indent=1, sort_keys=True)
    print("recorded %d metrics to %s" % (len(board), path))
    for key, value in sorted(board.items()):
        print("  %-40s %s" % (key, value))
    return 0


def cmd_check(path):
    with open(path) as handle:
        baseline = json.load(handle)
    report = full_report()
    board = _scoreboard(report)

    all_keys = sorted(set(baseline) | set(board))
    changed = []
    for key in all_keys:
        before = baseline.get(key, "(absent)")
        after = board.get(key, "(absent)")
        marker = "  " if before == after else ("UP" if _numeric_increase(before, after) else "DN")
        if before != after:
            changed.append(key)
        print("  %-40s %-15s -> %-15s %s" % (key, before, after, marker))
    print()
    if changed:
        print("%d of %d metrics changed since %s" % (len(changed), len(all_keys), path))
    else:
        print("no change in any of %d metrics since %s" % (len(all_keys), path))
    return 0


def _numeric_increase(before, after):
    try:
        return float(after) > float(before)
    except (TypeError, ValueError):
        return False


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if argv and argv[0] in ("record", "check"):
        if len(argv) < 2:
            print(__doc__)
            return 2
        return (cmd_record if argv[0] == "record" else cmd_check)(argv[1])

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--names", action="store_true")
    parser.add_argument("--duplication", action="store_true")
    parser.add_argument("--complexity", action="store_true")
    parser.add_argument("--misc", action="store_true")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    requested = [name for name in ("names", "duplication", "complexity", "misc")
                if getattr(args, name)]
    sections = requested or ["names", "duplication", "complexity", "misc"]

    files = python_files()
    report = {"files_scanned": len(files)}
    if "names" in sections:
        report["names"] = names_report(files)
    if "duplication" in sections:
        report["duplication"] = duplication_report(files)
    if "complexity" in sections:
        report["complexity"] = complexity_report(files)
    if "misc" in sections:
        report["misc"] = misc_report(files)

    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True))
    else:
        print_report(report, sections)
    return 0


if __name__ == "__main__":
    sys.exit(main())
