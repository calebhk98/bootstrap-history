"""SCENARIO (Complaint 640): Complaint 640, audit batch 3, scenario: firms pricing a chain of projects share its material bills, and a bill is
not served after the market moved. The rule (the shared-answer table) has tests of its own:
test_complaint_321_shared_project_bills."""
from .harness import *  # noqa: F401,F403
from sim.agents.api import Firm
from sim.engine.agents_port import SimWorld
from sim.agents import imitation
from sim.engine.project_materials import ProjectMaterialsMixin
from sim.engine.state import ActorRecord


def _chain_with_materials(game, length=4):
    chain = [node_id for node_id in ORDER if NODES[node_id].get("mat")][:length]
    game.state.projects.done.update(chain)
    game._done_changed()
    game.resource_throttle()  # the turn's held material demand, as a played year has it
    return chain


def _bill_computations(firm_count):
    """How many material purchases the bill code prices when `firm_count` firms price one chain."""
    game = unopened_sim(capital=1e9)
    chain = _chain_with_materials(game)
    world = SimWorld(game)
    purchases = [0]
    real_cost = ProjectMaterialsMixin.material_purchase_cost

    def counting_cost(self, *arguments, **keywords):
        purchases[0] += 1
        return real_cost(self, *arguments, **keywords)

    ProjectMaterialsMixin.material_purchase_cost = counting_cost
    try:
        plans = [imitation.copy_plan(Firm("probe:%d" % number, ActorRecord(kind="firm")), chain, world)
                 for number in range(firm_count)]
    finally:
        ProjectMaterialsMixin.material_purchase_cost = real_cost
    return purchases[0], plans


_few_count, _few_plans = _bill_computations(3)
_many_count, _many_plans = _bill_computations(40)
check("scenario shared bills: pricing one chain for forty firms computes no more bills than for three, "
      "and every firm is quoted the same copy cost",
      _few_count > 0 and _many_count == _few_count
      and all(plan["total"] == _many_plans[0]["total"] for plan in _many_plans), (_few_count, _many_count))

_game = unopened_sim(capital=1e9)
_chain = _chain_with_materials(_game)
_world = SimWorld(_game)
_first = _world.copy_cost(_chain[0])
for _material in sorted(NODES[_chain[0]]["mat"]):
    _game._material_stock()[_game._material_tag(_material)[0]] = 1.0e6
check("scenario shared bills: a cost asked of the same world view after the stock moved is the live one, "
      "and the view leaves no scope open on the founder's own pricing",
      _game.project_cost(_chain[0]) != _first and _world.copy_cost(_chain[0]) == _game.project_cost(_chain[0])
      and getattr(_game, "_view_scope", None) is None, (_first, _game.project_cost(_chain[0])))
