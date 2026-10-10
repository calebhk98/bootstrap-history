"""Complaint 369: a technique one producer runs reaches the other concerns in its line only after the copying
time, and the opening's techniques are held from the start."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.agents.api import imitation
from sim.engine import concern_volume, technique_spread
from sim.engine.techniques_in_use import TechniquesInUseMixin

QUICK_TOPIC = True

nodes = {"old_way": {"yrs": 2.0}, "new_way": {"yrs": 10.0}, "quick_way": {"yrs": 0.0}}
check("copying takes at least a year", imitation.copy_years(nodes["quick_way"]) == 1)
check("a longer invention takes longer to copy",
      imitation.copy_years(nodes["new_way"]) > imitation.copy_years(nodes["old_way"]))
years_needed = imitation.copy_years(nodes["new_way"])

first_run = {}
technique_spread.note_first_run(first_run, ["old_way"], 1000, True)
check("what is run when the record starts counts as spread",
      "old_way" in technique_spread.spread_techniques(["old_way"], [], first_run, nodes, 1000))
technique_spread.note_first_run(first_run, ["old_way", "new_way"], 1010, False)
check("a technique first run now is not yet copied",
      "new_way" not in technique_spread.spread_techniques(["old_way", "new_way"], [], first_run, nodes, 1010))
check("...nor one year short of the copying time",
      "new_way" not in technique_spread.spread_techniques(["new_way"], [], first_run, nodes, 1010 + years_needed - 1))
check("...but it is once the copying time has passed",
      "new_way" in technique_spread.spread_techniques(["new_way"], [], first_run, nodes, 1010 + years_needed))
check("the first sighting is not overwritten", first_run["new_way"] == 1010)
check("a technique the society started with is always held",
      "new_way" in technique_spread.spread_techniques([], ["new_way"], {}, nodes, 1010))

# --- the concern's entries follow the spread set
production = {
    "own": {"outputs": {"bar": 1.0}, "requires_node": "own_node", "operated_by": "own_node"},
    "better": {"outputs": {"bar": 1.0}, "requires_node": "new_way"},
}
own = frozenset({"own_node"})
check("a concern keeps its own entry until the other technique is copied",
      production["better"] not in concern_volume.entries_held_for("own_node", production, own))
check("...and gains the better one once it is",
      production["better"] in concern_volume.entries_held_for("own_node", production, own | {"new_way"}))

# --- the Sim method reads the economy record and the year
game = SimpleNamespace(
    state=SimpleNamespace(scenario=SimpleNamespace(year=1000), projects=SimpleNamespace(granted={"old_way"}),
                          economy=SimpleNamespace(technique_first_run={}, technique_record_started=False)),
    nodes=nodes, techniques_in_use=lambda: frozenset({"old_way", "new_way"}))
game.techniques_spread = lambda: TechniquesInUseMixin.techniques_spread(game)
check("at the opening every technique in use is spread", game.techniques_spread() == {"old_way", "new_way"})
game.techniques_in_use = lambda: frozenset({"old_way", "new_way", "quick_way"})
game.state.scenario.year = 1005
check("a technique that appears later waits", "quick_way" not in game.techniques_spread())
game.state.scenario.year = 1006
check("...then spreads", "quick_way" in game.techniques_spread())

# --- an opening with nothing running still starts the record, so the first later technique waits
empty = SimpleNamespace(
    state=SimpleNamespace(scenario=SimpleNamespace(year=1000), projects=SimpleNamespace(granted=set()),
                          economy=SimpleNamespace(technique_first_run={}, technique_record_started=False)),
    nodes=nodes, techniques_in_use=lambda: frozenset())
empty.techniques_spread = lambda: TechniquesInUseMixin.techniques_spread(empty)
check("an opening with no technique running is still the opening", empty.techniques_spread() == frozenset())
empty.techniques_in_use = lambda: frozenset({"new_way"})
empty.state.scenario.year = 1001
check("...so the first technique run after it waits its copying time", "new_way" not in empty.techniques_spread())
