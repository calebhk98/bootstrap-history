"""The lead time the hazard advice states: lead_time_range folds the open hedges' floors into one answer, and
HazardsMixin._calendar_floor_remaining (on a stand-in self holding the real tree) is what a hedge's chain still needs."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.engine.hazard_hedge_timing import lead_time_range
from sim.engine.society_hazards import HazardsMixin

check("several different floors are a quickest and a slowest", lead_time_range([30.0, 4.0, 12.0]) == {"quickest": 4.0, "slowest": 30.0})
check("floors that agree are the one figure", lead_time_range([7.0, 7.0]) == 7.0)
check("no open hedge has no answer", lead_time_range([]) is None)

standing = HazardsMixin._calendar_floor_remaining(SimpleNamespace(nodes=NODES, state=SimpleNamespace(projects=SimpleNamespace(done=set()))),
                                                  "academy_network")
partly = HazardsMixin._calendar_floor_remaining(
    SimpleNamespace(nodes=NODES, state=SimpleNamespace(projects=SimpleNamespace(done={"scientific_method", "corpus_written"}))),
    "academy_network")
check("the remaining floor is smaller by exactly the years of what is done",
      abs(partly - (standing - NODES["scientific_method"]["yrs"] - NODES["corpus_written"]["yrs"])) < 1e-6, (partly, standing))
check("a goal that is not in the tree has no floor",
      HazardsMixin._calendar_floor_remaining(SimpleNamespace(nodes=NODES, state=None), "not_a_node") is None)
