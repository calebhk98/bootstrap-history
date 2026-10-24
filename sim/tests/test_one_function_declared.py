"""A test calls one function on inputs it writes out; only a declared smoke test builds a game. The detector and the
declaration are called on source text built here; the last two checks read the tree against the shrinking list."""
QUICK_TOPIC = True

from .harness import check
from sim.tests import one_function_checks as guard


def calls_of(source):
    return [name for _, name in guard.setup_calls(source)]


for call, expected in (("sim()", "sim"), ("unopened_sim('rome_100ad')", "unopened_sim"), ("Economy(setup)", "Economy"),
                       ("game.labour.hire('smith', 5)", "....hire"),
                       ("fixture.run(setup, 3)", "fixture.run"), ("years_of(setup, 4)", "years_of"),
                       ("game.open_venture('kiln')", "game.open_venture")):
    check("a call to %s counts as setup through another function" % call, calls_of("x = %s\n" % call) == [expected],
          calls_of("x = %s\n" % call))

check("a unit's own step is a function under test, not setup", calls_of("population.step(food)\n") == [])
check("a module that calls only the function under test has no setup calls",
      calls_of("from sim.engine.payroll_shed import shed_unpayable_staff\nstate = {'smith': 5}\n"
               "shed_unpayable_staff(state, cash=0.0)\n") == [])
check("a module that defines its own helper of a setup name is not charged for it",
      calls_of("def step(record):\n    return record\n\nstep({})\n") == [])
check("a function that takes the builder as a parameter is not charged for calling it",
      calls_of("def run(sim):\n    return sim()\n") == [])
check("a command a module declares UNDER_TEST is its function under test, not setup",
      calls_of("UNDER_TEST = {'commission_mines'}\ngame.commission_mines(plan)\n") == [])
check("...but a game builder cannot be declared under test",
      calls_of("UNDER_TEST = {'sim'}\ngame = sim()\n") == ["sim"])
check("a mention in a string or comment is not a call", calls_of("# game = sim()\nnote = 'hire(smith)'\n") == [])

check("a file name ending _smoke declares a smoke test", guard.is_smoke("opening_smoke", "game = sim()\n"))
check("a docstring opening SMOKE declares a smoke test", guard.is_smoke("opening", '"""SMOKE: one year.\n"""\n'))
check("a scenario is not a smoke test", not guard.is_smoke("freight_scenario", '"""SCENARIO: a year.\n"""\n'))

check("an offender not in the list is new, and a listed topic that stopped offending is stale",
      guard.differences({"a": ((1, "sim"), 1), "b": ((2, "sim"), 1)}, {"b", "c"}) == (["a"], ["c"]))

new, stale = guard.differences(guard.offending_modules(), guard.listed_leftovers())
check("no new module reaches its function through other engine functions: build the inputs and call the one function",
      not new, new)
check("no stale leftovers entry: delete the line of a module that now calls only its function", not stale, stale)
