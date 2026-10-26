"""The resources module's mine_works_effects: the combined effect of the running mining techniques is computed once and read
from the kept table until what is built or operating changes."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.tests import resources_stand_in

asked = []
stamp = [("projects", (0, 0, 0, 0, 0), "nodes")]


def running(node_id):
    asked.append(node_id)
    return node_id == "pump"


world = resources_stand_in.build(views={
    "running": running, "running_stamp": lambda: stamp[0],
    "effect_terms": lambda key: [("pump", {"drainage_lift_efficiency": 0.5, "gravity_drained_head_share": 0.0}),
                                 ("idle", {"drainage_lift_efficiency": 0.9})]})
first = world.mine_works_effects()
asked_first = len(asked)
for _ in range(20):
    world.mine_works_effects()
check("the effects of running techniques only are combined: the idle one does not count",
      first.get("drainage_lift_efficiency", 0.0) != 0.9, first)
check("a repeated read asks no node whether it runs", len(asked) == asked_first and asked_first == 2, asked)
stamp[0] = ("projects", (1, 0, 0, 0, 0), "nodes")
world.mine_works_effects()
check("a change in what operates makes the next read recompute", len(asked) == 2 * asked_first, asked)
