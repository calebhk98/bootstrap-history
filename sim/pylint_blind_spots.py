"""Short names that `python3 -m pylint sim/` reports nothing about.

WHY THIS EXISTS. `.pylintrc` turns pylint into a worklist for CLAUDE.md
section 7 - every short name comes back as a file:line somebody can fix.
It got the tree to zero findings. Zero findings is not a tree without short
names, and the difference is large enough that somebody was always going to
read the first as the second.

Pylint's `invalid-name` check is driven by how pylint CLASSIFIES a binding,
and three classifications have no name check at all:

    KB = os.path.join("a", "b")   module-level name bound to a CALL   invisible
    QQ = 5                        module-level name bound to a LITERAL   reported
    for p in items:               module-level loop target            invisible
    lambda a: a + 1               lambda parameter                    invisible
    def g(): ...                  function                               reported
        for z in items:           function-level loop target             reported

The two module-level rows differ only in what is on the right of the `=`.
That is not a rule anybody would choose; it is what pylint's constant-versus-
variable inference happens to do, and it means the checker is quietest
exactly where this codebase keeps most of its short names, because the test
suite is written as module-level script code rather than as functions.

So: run pylint for the worklist, run THIS for the size of what pylint cannot
see, and run `python3 sim/code_health.py --names` for the burndown total that
covers both.

    python3 sim/pylint_blind_spots.py            counts, with one example each
    python3 sim/pylint_blind_spots.py --list     every site, as file:line name
"""

import ast, os, sys, collections

SHORT_ENOUGH_TO_BE_A_PROBLEM = 2

# CLAUDE.md section 7's own exemptions. `i` as a loop index and `x`/`y` as
# coordinates are allowed, so counting them here would report work that the
# working agreement says is not work.
#
# This is slightly MORE generous than section 7, which allows them "only
# inside a scope short enough to see whole" - a judgement no script can
# make. The effect is that this count is a floor: a module-level `i`
# spanning two hundred lines is a real finding and is not counted here.
EXEMPT = {"i", "x", "y"}

# Length is measured AFTER stripping underscores, so `_k` and `__q` count
# and `_ab` does too. A leading underscore is a visibility marker, not a
# character that helps a reader work out what the name holds.


def _is_short(name):
    if not name:
        return False
    stripped = name.strip("_")
    return bool(stripped) and len(stripped) <= SHORT_ENOUGH_TO_BE_A_PROBLEM \
        and stripped not in EXEMPT


# WHICH MODULE-LEVEL ASSIGNMENTS PYLINT ALREADY REPORTS, so this script does
# not count work that is on pylint's worklist. Measured against pylint with
# this repository's .pylintrc, one value shape per line:
#
#     reported as a Constant: 5   "text"   None   True   1 + 2   f"x"   os.sep
#     not reported:  (1, 2)  [1, 2]  {"a": 1}  {1, 2}  os.path.join("a")
#                    lambda q: q   [n for n in range(3)]
#
# The rule is astroid's INFERENCE, not the syntax: `os.sep` is reported
# because astroid follows it to a string. A script parsing one file cannot
# follow that, so this function deliberately guesses "pylint reports it"
# for every Name and Attribute as well. That UNDER-counts - a module-level
# `PATHS = SOME_LIST` is a real short name nothing reports - and
# under-counting is the right way to be wrong here, because the whole claim
# this script makes is "there is more than pylint shows". A number that
# could be inflated by double-counting would not support it.
_ALWAYS_A_CONSTANT_TO_PYLINT = (ast.Constant, ast.JoinedStr, ast.BinOp,
                                ast.UnaryOp, ast.Name, ast.Attribute)


def _pylint_calls_it_a_constant(value):
    return isinstance(value, _ALWAYS_A_CONSTANT_TO_PYLINT)


def _nested_node_ids(tree):
    """Every node that sits inside a def, class or lambda.

    Used to tell a module-level binding from one inside a scope, which is
    the whole distinction this script is about. Identity is safe here
    because the tree is alive for the entire walk - unlike the id() trap in
    CLAUDE.md section 6, nothing is freed underneath us.
    """
    inside = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Lambda)):
            for child in ast.walk(node):
                if child is not node:
                    inside.add(id(child))
    return inside


def blind_spots(root="sim"):
    """{category: [(path, line, name)]} for what pylint will not report."""
    found = collections.defaultdict(list)
    for directory, _subdirs, filenames in os.walk(root):
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            path = os.path.join(directory, filename)
            try:
                tree = ast.parse(open(path).read())
            except SyntaxError:
                continue
            inside = _nested_node_ids(tree)
            for node in ast.walk(tree):
                at_module_level = id(node) not in inside
                if isinstance(node, ast.Lambda):
                    for argument in node.args.args:
                        if _is_short(argument.arg):
                            found["lambda parameter"].append(
                                (path, node.lineno, argument.arg))
                if not at_module_level:
                    continue
                if isinstance(node, ast.For) and isinstance(node.target, ast.Name) \
                        and _is_short(node.target.id):
                    found["module-level loop target"].append(
                        (path, node.lineno, node.target.id))
                if isinstance(node, ast.Assign) and not _pylint_calls_it_a_constant(node.value):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and _is_short(target.id):
                            found["module-level assignment"].append(
                                (path, target.lineno, target.id))
    return found


def main(argv):
    found = blind_spots()
    if "--list" in argv:
        for category in sorted(found):
            print("# %s" % category)
            for path, line, name in found[category]:
                print("%s:%d %s" % (path, line, name))
        return 0
    total = 0
    for category, sites in sorted(found.items(), key=lambda pair: -len(pair[1])):
        total += len(sites)
        path, line, name = sites[0]
        print("%-28s %4d   e.g. %s:%d  %s" % (category, len(sites), path, line, name))
    print("%-28s %4d   (pylint reports none of these)" % ("total", total))
    return 0


if __name__ == "__main__":
    # --list exists to be piped into head, grep or a pager, and every one of
    # those closes the pipe early. Without this the script dies on a
    # BrokenPipeError traceback that looks like a bug in the scan.
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        try:
            sys.stdout.close()
        finally:
            os._exit(0)
