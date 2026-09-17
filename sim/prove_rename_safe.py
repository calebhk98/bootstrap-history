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

This repository has 4,972 occurrences of identifiers two characters or
shorter. Fixing them means touching nearly every file, and the usual way to
show a refactor was safe - run `perf_fingerprint.py` before and after - cannot
be used, for two separate reasons. It does not currently reproduce its own
recording (Complaints/27). And even when it does, it is evidence rather than
proof: it says nine reference runs came out the same, not that no behaviour
anywhere could differ.

For renaming local variables there is something much stronger available, and
it comes free from how CPython compiles.

**A local variable's name is not in the bytecode.** Locals are addressed by
slot index - `LOAD_FAST 3`, not `LOAD_FAST "capital"` - and the names live in
a separate table, `co_varnames`, used for introspection and tracebacks. Rename
a local and `co_code`, the actual executed bytes, does not change at all.

Attributes and globals are the opposite: `LOAD_ATTR` and `LOAD_GLOBAL` carry
an index into `co_names`, which holds the actual strings. Touch an attribute
and `co_names` changes. String literals and numbers live in `co_consts`.

So the comparison is:

    co_code    must be byte-identical      (the logic)
    co_names   must be identical           (attributes, globals, methods)
    co_consts  must be identical           (literals, and nested functions,
                                             compared recursively)
    co_varnames  MAY differ                (that is the rename)

If all three hold, the two files execute the same instructions against the
same attributes with the same constants. That is not a sample of nine runs.
It is every possible run.

WHAT IT DOES NOT COVER, and you must read this before trusting it:

  * **Only local renames.** Renaming an attribute, a parameter that callers
    pass by keyword, a global, a dict key or a string is a real change and
    this tool will correctly refuse it. That is the point - it is the
    Tier 1 / Tier 2 boundary from docs/architecture/NAMING_PLAN.md, enforced
    mechanically instead of by eye.
  * **Not keyword arguments.** A parameter rename leaves `co_code` alone in
    the DEFINING function, so this tool passes it, while any caller using
    `f(s=...)` breaks. Parameters are Tier 2 for exactly this reason.
    `--check-params` reports which renamed locals are parameters, so you can
    check their call sites by hand.
  * **Docstrings yes, COMMENTS NO.** A docstring is `co_consts[0]`, so editing
    one fails this check - correct, if occasionally annoying, and the reason to
    keep a rename commit free of prose edits.

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
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def code_objects(code, path=""):
    """Every code object in a module, depth first, with a readable path."""
    name = "%s.%s" % (path, code.co_name) if path else code.co_name
    yield name, code
    for const in code.co_consts:
        if hasattr(const, "co_code"):
            for item in code_objects(const, name):
                yield item


def compile_source(source, filename):
    return compile(source, filename, "exec", dont_inherit=True)


def _consts_without_code(code):
    """co_consts with nested code objects removed - those compare separately."""
    return tuple(c for c in code.co_consts if not hasattr(c, "co_code"))


def compare(before_source, after_source, filename):
    """Return a list of differences that are NOT a local rename."""
    try:
        before = compile_source(before_source, filename)
    except SyntaxError as exc:
        return ["the OLD version does not compile: %s" % exc]
    try:
        after = compile_source(after_source, filename)
    except SyntaxError as exc:
        return ["the NEW version does not compile: %s" % exc]

    before_by_name = dict(code_objects(before))
    after_by_name = dict(code_objects(after))

    problems = []
    only_before = sorted(set(before_by_name) - set(after_by_name))
    only_after = sorted(set(after_by_name) - set(before_by_name))
    for name in only_before:
        problems.append("function disappeared or was renamed: %s" % name)
    for name in only_after:
        problems.append("function appeared or was renamed: %s" % name)

    for name in sorted(set(before_by_name) & set(after_by_name)):
        old, new = before_by_name[name], after_by_name[name]
        if old.co_code != new.co_code:
            problems.append("%s: the BYTECODE changed - this is not a rename, "
                            "it is a behaviour change" % name)
        if old.co_names != new.co_names:
            gone = sorted(set(old.co_names) - set(new.co_names))
            added = sorted(set(new.co_names) - set(old.co_names))
            problems.append(
                "%s: an ATTRIBUTE or GLOBAL changed, not a local - removed %s, "
                "added %s. That is Tier 2 or 3; verify it another way."
                % (name, gone or "nothing", added or "nothing"))
        if _consts_without_code(old) != _consts_without_code(new):
            problems.append("%s: a CONSTANT changed - a literal, a string, a "
                            "dict key or a docstring. Make prose edits in a "
                            "separate commit." % name)
    return problems


def renamed_parameters(before_source, after_source, filename):
    """Renamed locals that are also parameters: callers may pass by keyword."""
    before = compile_source(before_source, filename)
    after = compile_source(after_source, filename)
    before_by_name = dict(code_objects(before))
    after_by_name = dict(code_objects(after))
    flagged = []
    for name in sorted(set(before_by_name) & set(after_by_name)):
        old, new = before_by_name[name], after_by_name[name]
        count = old.co_argcount + old.co_kwonlyargcount
        for old_arg, new_arg in zip(old.co_varnames[:count],
                                    new.co_varnames[:count]):
            if old_arg != new_arg:
                flagged.append("%s: parameter %s -> %s" % (name, old_arg, new_arg))
    return flagged


def git_show(ref, path):
    result = subprocess.run(["git", "show", "%s:%s" % (ref, path)],
                            capture_output=True, text=True, cwd=ROOT)
    return result.stdout if result.returncode == 0 else None


def python_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "sim")):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
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
