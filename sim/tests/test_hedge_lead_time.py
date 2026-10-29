"""The lead time the hazard advice states: lead_time_range folds the open hedges' floors into one answer, and the hazards
module's calendar_floor_remaining (over the real tree) is what a hedge's chain still needs."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.knowledge.api import critical_path
from sim.hazards.hedge_timing import lead_time_range
from sim.tests import hazards_host

check("several different floors are a quickest and a slowest", lead_time_range([30.0, 4.0, 12.0]) == {"quickest": 4.0, "slowest": 30.0})
check("floors that agree are the one figure", lead_time_range([7.0, 7.0]) == 7.0)
check("no open hedge has no answer", lead_time_range([]) is None)


def module_holding(done):
    return hazards_host.build(tree_nodes=NODES, techniques_held=set(done), critical_path=lambda goal: critical_path(NODES, goal))


standing = module_holding(set()).calendar_floor_remaining("academy_network")
partly = module_holding({"scientific_method", "corpus_written"}).calendar_floor_remaining("academy_network")
check("the remaining floor is smaller by exactly the years of what is done",
      abs(partly - (standing - NODES["scientific_method"]["yrs"] - NODES["corpus_written"]["yrs"])) < 1e-6, (partly, standing))
check("a goal that is not in the tree has no floor", module_holding(set()).calendar_floor_remaining("not_a_node") is None)
