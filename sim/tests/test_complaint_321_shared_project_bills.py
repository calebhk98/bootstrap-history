"""Complaint 321: what a project costs in materials does not depend on the firm
pricing it, so a yearly turn computes each project's material bill once however
many firms price it, and never serves a bill the market has since moved under."""
from .harness import *  # noqa: F401,F403
from sim.engine.actors import SimWorld, Firm, imitation
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
    game = sim(capital=1e9)
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


few_count, few_plans = _bill_computations(3)
many_count, many_plans = _bill_computations(40)
check("set-up: the chain buys materials, so pricing it costs purchase quotes", few_count > 0, few_count)
check("pricing one chain for forty firms computes no more bills than for three",
      many_count == few_count, (few_count, many_count))
check("every firm is quoted the same copy cost for the same chain",
      all(plan["total"] == many_plans[0]["total"] for plan in many_plans))

# --- a bill is not served after the market it was priced in moved -----------
game = sim(capital=1e9)
chain = _chain_with_materials(game)
world = SimWorld(game)
first = world.copy_cost(chain[0])
for material in sorted(NODES[chain[0]]["mat"]):
    game._material_stock()[game._material_tag(material)[0]] = 1.0e6
check("set-up: the held stock moved the cost", game.project_cost(chain[0]) != first, first)
check("a cost asked of the same world view after the stock moved is the live one",
      world.copy_cost(chain[0]) == game.project_cost(chain[0]),
      (world.copy_cost(chain[0]), game.project_cost(chain[0]), first))

# --- the founder's own pricing is not touched by the shared table -----------
game = sim(capital=1e9)
chain = _chain_with_materials(game)
before = game.project_cost(chain[0])
SimWorld(game).copy_cost(chain[0])
check("a view's shared bills leave no scope open on the founder's own pricing",
      getattr(game, "_view_scope", None) is None and game.project_cost(chain[0]) == before)
