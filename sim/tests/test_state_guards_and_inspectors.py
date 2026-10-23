"""Complaint 660: order against theft and the mine ceiling follow the guards and inspectors a state employs and pays,
not the share its officials collect. The rules are called on built inputs; the home game is in test_state_guards_and_inspectors_scenario."""
from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

from sim.agents import budget, collection, order
from sim.engine.mine_ceiling import mine_ceiling_tonnes
from sim.engine.theft_exposure import order_factor
from .agents_fake_world import FakeWorld

WORKING_DAYS = 200.0
PEOPLE = {"seat": 10_000.0, "near": 10_000.0, "far": 10_000.0}
DAYS = {"seat": 0.0, "near": 2.0, "far": 40.0}
PATROL = 0.01


def shares_for(staff, days=DAYS, per_person=PATROL):
    return collection.tile_shares(staff, WORKING_DAYS, 0.0, PEOPLE, days, person_days=per_person)


# ---- the time guards have: more guards or a nearer tile lowers the theft left on that tile ----------------------
few, many = shares_for(1.0), shares_for(2.0)
check("more guards raise the share of a tile under watch", many["far"] > few["far"] and many["near"] >= few["near"], (few, many))
check("a nearer tile is watched more than a far one", few["near"] > few["far"], few)
check("a watch is never more than all of the tile", max(shares_for(1.0e6).values()) <= 1.0)
check("no guards watch nothing", sum(shares_for(0.0).values()) == 0.0)
check("the same guards at a nearer tile leave less theft",
      order_factor(shares_for(1.0, days=dict(DAYS, far=4.0))["far"], 0.0) < order_factor(few["far"], 0.0))
check("more guards leave less theft on the tile", order_factor(many["far"], 0.0) < order_factor(few["far"], 0.0))

# ---- foresters keep woodland tenure by the same time rule; the forest ceiling reads their reach ---------------------
from sim.engine.forest_ceiling import forest_ceiling_hectares

check("more foresters raise the share of a tile whose woodland is kept",
      shares_for(2.0, per_person=order.FORESTER_DAYS_PER_PERSON)["far"] > shares_for(1.0, per_person=order.FORESTER_DAYS_PER_PERSON)["far"])
check("no foresters keep nothing", sum(shares_for(0.0, per_person=order.FORESTER_DAYS_PER_PERSON).values()) == 0.0)
check("more forester reach raises the forest ceiling",
      forest_ceiling_hectares(1.0e6, 0.8, 1000.0, 2000.0, 1.0) > forest_ceiling_hectares(1.0e6, 0.3, 1000.0, 2000.0, 1.0))

# ---- inspectors raise the mine ceiling ----------------------------------------------------------------------------
terms = {"base": 1000.0, "state_scale": 5000.0}
check("more inspectors raise the mine ceiling",
      mine_ceiling_tonnes(terms, 0.8, 0, 0, 1.0, 1.0) > mine_ceiling_tonnes(terms, 0.3, 0, 0, 1.0, 1.0))

# ---- the staff are kept and paid like any line: employed = kept less the unpaid share -------------------------------
check("staff on the payroll are those kept less the share of their pay left unpaid",
      collection.officials_employed(100.0, 1000.0, 250.0) == 75.0)


class OrderWorld(FakeWorld):
    def population_total(self):
        return 40_000.0

    def pay_per_person_year(self, trade):
        return 10.0

    def national_people(self, trade):
        return 1.0e9


world = OrderWorld()
guards = order.guards_kept(world.population_total(), WORKING_DAYS)
inspectors = order.inspectors_kept(world.population_total(), WORKING_DAYS)
check("guards kept follow the people and the days one person's watch takes",
      abs(guards - 40_000.0 * order.PATROL_DAYS_PER_PERSON / WORKING_DAYS) < 1e-9, guards)
check("no people need no guards and no inspectors", order.guards_kept(0.0, WORKING_DAYS) == 0.0 and order.inspectors_kept(0.0, WORKING_DAYS) == 0.0)
by_name = {line.name: line for line in order.guards_line(world) + order.inspectors_line(world) + order.foresters_line(world)}
foresters = order.foresters_kept(world.population_total(), WORKING_DAYS)
check("the state keeps a guards, an inspectors and a foresters line", {"guards", "inspectors", "foresters"} == set(by_name), sorted(by_name))
check("the foresters line pays the foresters kept at the going wage",
      abs(by_name["foresters"].wages - foresters * 10.0) < 1e-6 and by_name["foresters"].transfer == 0.0, by_name["foresters"])
check("no people need no foresters", order.foresters_kept(0.0, WORKING_DAYS) == 0.0)
check("the guards line pays the guards kept at the going wage",
      abs(by_name["guards"].wages - guards * 10.0) < 1e-6 and abs(sum(by_name["guards"].labour.values()) - guards) < 1e-9,
      by_name["guards"])
check("the inspectors line pays the inspectors kept at the going wage",
      abs(by_name["inspectors"].wages - inspectors * 10.0) < 1e-6
      and abs(sum(by_name["inspectors"].labour.values()) - inspectors) < 1e-9, by_name["inspectors"])
check("both are staff the state hires, not a transfer", by_name["guards"].transfer == 0.0 and by_name["inspectors"].transfer == 0.0)
