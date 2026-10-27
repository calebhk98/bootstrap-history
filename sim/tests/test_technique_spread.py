"""Complaint 369: a technique one producer runs reaches the other concerns in its line only after the copying
time, and the opening's techniques are held from the start."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.agents.api import imitation
from sim.diffusion import technique_spread
from sim.production import volume_rules as concern_volume
from sim.diffusion.api import NoteFirstRuns
from sim.diffusion.module import Diffusion
from sim.diffusion.state import DiffusionWorld
from sim.tests import module_harness

QUICK_TOPIC = True

nodes = {"old_way": {"yrs": 2.0}, "new_way": {"yrs": 10.0}, "quick_way": {"yrs": 0.0}}
check("copying takes at least a year", imitation.copy_years(nodes["quick_way"]) == 1)
check("a longer invention takes longer to copy",
      imitation.copy_years(nodes["new_way"]) > imitation.copy_years(nodes["old_way"]))
years_needed = imitation.copy_years(nodes["new_way"])

first_run = {}
technique_spread.note_first_run(first_run, ["old_way"], 1000, True)
check("what is run when the record starts counts as spread",
      "old_way" in technique_spread.spread_techniques(["old_way"], [], first_run, nodes.get, 1000))
technique_spread.note_first_run(first_run, ["old_way", "new_way"], 1010, False)
check("a technique first run now is not yet copied",
      "new_way" not in technique_spread.spread_techniques(["old_way", "new_way"], [], first_run, nodes.get, 1010))
check("...nor one year short of the copying time",
      "new_way" not in technique_spread.spread_techniques(["new_way"], [], first_run, nodes.get, 1010 + years_needed - 1))
check("...but it is once the copying time has passed",
      "new_way" in technique_spread.spread_techniques(["new_way"], [], first_run, nodes.get, 1010 + years_needed))
check("the first sighting is not overwritten", first_run["new_way"] == 1010)
check("a technique the society started with is always held",
      "new_way" in technique_spread.spread_techniques([], ["new_way"], {}, nodes.get, 1010))

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

# --- the module stamps first sightings by command and answers from the record, the year and what is granted
def spread_host(granted, in_use, year):
    """A diffusion module over fixed views, and a function that notes and asks as the game does."""
    now = {"year": year, "in_use": frozenset(in_use)}
    module = module_harness.build(
        Diffusion, world=DiffusionWorld(),
        views={"year": lambda: now["year"], "tree": nodes.get, "techniques_granted": lambda: granted,
               "techniques_in_use": lambda: now["in_use"]})

    def spread():
        module.note_first_runs(NoteFirstRuns(now["in_use"]))
        return module.techniques_spread()
    return now, spread


now, spread = spread_host({"old_way"}, {"old_way", "new_way"}, 1000)
check("at the opening every technique in use is spread", spread() == {"old_way", "new_way"})
now["in_use"] = frozenset({"old_way", "new_way", "quick_way"})
now["year"] = 1005
check("a technique that appears later waits", "quick_way" not in spread())
now["year"] = 1006
check("...then spreads", "quick_way" in spread())

# --- an opening with nothing running still starts the record, so the first later technique waits
now, spread = spread_host(set(), set(), 1000)
check("an opening with no technique running is still the opening", spread() == frozenset())
now["in_use"] = frozenset({"new_way"})
now["year"] = 1001
check("...so the first technique run after it waits its copying time", "new_way" not in spread())
