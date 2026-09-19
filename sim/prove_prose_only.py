#!/usr/bin/env python3
"""Prove a change touched only prose, never executable code.

    python3 sim/prove_prose_only.py <file> [<file> ...]
    python3 sim/prove_prose_only.py $(git diff --name-only -- '*.py')

Exit status 0 means every named file is unchanged apart from comments and
docstrings. Exit status 1 names the files where something executable moved.

WHY THIS EXISTS. This codebase is 30-50% prose by line, and the comments are
load-bearing (CLAUDE.md section 6), so large comment-only passes are a normal
kind of work here. The reviewer's problem with such a pass is that the diff is
enormous and the one thing that matters, whether any behaviour changed, is
invisible inside it. Reading a 200-line diff to confirm that nothing outside
the comments moved is exactly the job a machine should do.

HOW IT WORKS, AND WHAT THAT BUYS. Both versions are parsed, every docstring
is deleted from the resulting syntax tree, and the two trees are compared.
Comments never reach a Python AST at all, so a comment edit is invisible here
by construction rather than by a rule this file has to get right. Docstrings
do reach it, as the first statement of a module, class or function, so they
are removed deliberately.

What survives the strip is every expression, statement, name, literal and
argument. So a rename, a reordered pair of statements, a changed constant, a
dropped line, or an `if` whose condition was edited all show up, including the
case a line-based diff cannot see: a code line accidentally absorbed into a
comment block while rewrapping a paragraph around it.

RELATIONSHIP TO prove_rename_safe.py. That tool answers the opposite
question: it proves a rename changed nothing but NAMES, by comparing compiled
bytecode, and it deliberately REFUSES when a docstring changed, because a
docstring is `co_consts[0]` and a constant moving is indistinguishable from
the literal changes it is built to catch. Its refusal message says to make
prose edits in a separate commit.

That refusal is the reason this file exists. The two tools cover the two
halves of that separation and neither subsumes the other:

    prove_rename_safe.py   names may move, prose may not
    prove_prose_only.py    prose may move, names may not

Use this one on the prose commit, that one on the rename commit. A pass that
did both at once can be proven by neither.

LIMITS, STATED PLAINLY. A docstring is data: code can read `__doc__`, and at
least one thing in this repository does (`solve_prices.py`'s `main()` builds
its `--help` description from a module docstring's first line). This tool
calls such an edit prose, because syntactically it is. If a docstring is
load-bearing, the test suite is what catches it, and the suite must be run
alongside this.

Comparison is against the working tree's `HEAD` version of each file, so a
file that does not exist at `HEAD` is reported as new and skipped rather than
failing.
"""
import ast
import subprocess
import sys


def syntax_tree_without_docstrings(source, filename):
    """Parse `source` and return a dump of its AST with docstrings removed.

    A body emptied by the removal gets a `Pass` so the tree stays valid;
    `Pass` is inserted identically on both sides of any comparison, so it
    cannot mask a difference.
    """
    tree = ast.parse(source, filename=filename)
    holders = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    for node in ast.walk(tree):
        if not isinstance(node, holders):
            continue
        body = node.body
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    return ast.dump(ast.fix_missing_locations(tree))


def syntax_tree_with_every_string_blanked(source, filename):
    """As above, but every string literal anywhere is replaced by a marker.

    This answers the weaker question "did anything change except the TEXT of
    strings", which is what separates an edited `source=` argument from an
    edited `if` condition.
    """
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            node.value = "<string literal>"
    return ast.dump(ast.fix_missing_locations(tree))


def compare_against_head(path, revision="HEAD"):
    """Return "prose", "strings", "code" or "new" for one file.

    THE MIDDLE VERDICT EXISTS BECAUSE OF `declare()`. A docstring is prose in
    a place the parser recognises as prose. A string ARGUMENT is prose in a
    place the parser recognises as data, and this project is full of them:
    every `declare(...)` call carries `why=` and `source=` fields whose whole
    job is to explain a number in English, and `sim/tests/` passes a
    sentence-long description as the first argument of every `check(...)`.

    Editing one of those is a prose edit by intent and a data edit by fact,
    so calling it "code changed" is misleading and calling it "prose only" is
    false. It gets its own answer, and the distinction matters because the
    two carry different risk: nothing reads a docstring, whereas a `source=`
    string is stored in the registry `python3 sim/constants.py` prints, and a
    `check()` name string is matched on and printed by the suite. A reviewer
    seeing "strings" should confirm nothing depends on the exact wording;
    seeing "prose only" they need not.
    """
    committed = subprocess.run(["git", "show", "%s:%s" % (revision, path)],
                               capture_output=True, text=True)
    if committed.returncode:
        return "new"
    with open(path) as handle:
        working = handle.read()
    if (syntax_tree_without_docstrings(committed.stdout, path)
            == syntax_tree_without_docstrings(working, path)):
        return "prose"
    if (syntax_tree_with_every_string_blanked(committed.stdout, path)
            == syntax_tree_with_every_string_blanked(working, path)):
        return "strings"
    return "code"


def main(argv):
    if not argv:
        sys.stderr.write(__doc__.split("\n\n")[1] + "\n")
        return 2
    changed_code = []
    for path in argv:
        verdict = compare_against_head(path)
        print("%-44s %s" % (path, {
            "prose": "prose only",
            "strings": "prose, plus the text of string arguments",
            "code": "*** EXECUTABLE CODE CHANGED ***",
            "new": "new file, nothing at HEAD to compare",
        }[verdict]))
        if verdict == "code":
            changed_code.append(path)
    if changed_code:
        print("\n%d file(s) changed executable code. A prose-only pass should "
              "change none; if the change was deliberate, it belongs in its "
              "own commit." % len(changed_code))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
