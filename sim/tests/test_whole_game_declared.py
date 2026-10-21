"""Complaint 640: a test module that builds a whole game says so (a `_scenario`, `_validation` or `_smoke` file name, or a
docstring opening `SCENARIO`, `BASELINE VALIDATION` or `SMOKE`), or sits in the shrinking leftovers list. The detector and
the declaration are rules called on source text built here; the last two checks read the tree."""
QUICK_TOPIC = True

from .harness import check
from sim.tests import whole_game_checks as guard

BUILDS = "from .harness import *\ngame = sim()\n"


def builds_of(source):
    return [name for _, name in guard.game_builds(source)]


for call, expected in (("sim()", "sim"), ("unopened_sim('rome_100ad')", "unopened_sim"), ("harness.sim()", "harness.sim"),
                       ("S.Sim(NODES, ORDER)", "S.Sim"), ("Sim(NODES, ORDER)", "Sim"),
                       ("proto([{'cmd': 'why'}])", "proto"), ("cli_in_process.run(['agent'])", "cli_in_process.run"),
                       ("build_unopened(lambda: None)", "build_unopened"),
                       ("spin_up.spin_up_trace('rome_100ad')", "spin_up.spin_up_trace")):
    check("a call to %s counts as building a whole game" % call, builds_of("game = %s\n" % call) == [expected],
          builds_of("game = %s\n" % call))

check("a module that calls only the rule builds no game",
      builds_of("from x import rule\nassert rule(3) == 4\nsubprocess.run(['ls'])\n") == [])
check("a module that defines its own helper of a builder's name is not charged for it",
      builds_of("def sim():\n    return object()\n\nstand_in = sim()\n") == [])
check("a function that takes the builder as a parameter is not charged for calling it",
      builds_of("def run(sim):\n    return sim()\n") == [])
check("a mention in a string or comment is not a build", builds_of("# game = sim()\nnote = 'sim()'\n") == [])

check("a file name ending _scenario declares the module", guard.is_declared("freight_scenario", BUILDS))
check("a file name ending _validation declares the module", guard.is_declared("price_band_validation", BUILDS))
check("a file name ending _smoke declares the module", guard.is_declared("opening_smoke", BUILDS))
check("a docstring opening SCENARIO declares the module",
      guard.is_declared("freight", '"""SCENARIO: a year.\n"""\n' + BUILDS))
check("a docstring opening BASELINE VALIDATION declares the module",
      guard.is_declared("freight", '"""BASELINE VALIDATION (CLAUDE.md 4.2): a band.\n"""\n' + BUILDS))
check("a docstring that only mentions a scenario does not declare the module",
      not guard.is_declared("freight", '"""One scenario at the end.\n"""\n' + BUILDS))
check("a module with no docstring and a plain name is undeclared", not guard.is_declared("freight", BUILDS))

check("a builder not in the leftovers list is new, and a listed topic that stopped building is stale",
      guard.differences({"a": (1, "sim"), "b": (2, "sim")}, {"b", "c"}) == (["a"], ["c"]))
check("a list equal to the found modules has no difference", guard.differences({"a": (1, "sim")}, {"a"}) == ([], []))

new, stale = guard.differences(guard.undeclared_modules(), guard.listed_leftovers())
check("no new undeclared whole-game module: declare it, or build its inputs and call the rule", not new, new)
check("no stale leftovers entry: delete the line of a module that is declared, converted or gone", not stale, stale)
