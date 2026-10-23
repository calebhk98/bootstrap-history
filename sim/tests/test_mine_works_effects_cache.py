"""MiningMixin.mine_works_effects on a stand-in self: the combined effect of the running mining techniques is computed once
and read from the kept table until what is built or operating changes."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.engine.economy_mining import MiningMixin


class StandIn(MiningMixin):
    """The parts of a Sim the kept table and the effects read."""

    def __init__(self):
        self.state = SimpleNamespace(projects=SimpleNamespace(done=set(), granted=set(), operating=set()))
        self.household = SimpleNamespace(done_version=0, operating_version=0)
        self.nodes = {}
        self.asked = []

    def _effect_terms(self, key):
        return [("pump", {"drainage_lift_efficiency": 0.5, "gravity_drained_head_share": 0.0}),
                ("idle", {"drainage_lift_efficiency": 0.9})]

    def running(self, node_id):
        self.asked.append(node_id)
        return node_id == "pump"


world = StandIn()
first = world.mine_works_effects()
asked_first = len(world.asked)
for _ in range(20):
    world.mine_works_effects()
check("the effects of running techniques only are combined: the idle one does not count",
      first.get("drainage_lift_efficiency", 0.0) != 0.9, first)
check("a repeated read asks no node whether it runs", len(world.asked) == asked_first and asked_first == 2, world.asked)
world.household.operating_version += 1
world.mine_works_effects()
check("a change in what operates makes the next read recompute", len(world.asked) == 2 * asked_first, world.asked)
