"""Complaint 660: order against theft and the mine ceiling follow the guards and inspectors a state employs and pays,
not the share its officials collect. The rules are called on built inputs; one named scenario checks the home game."""
from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

sim = unopened_sim

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
by_name = {line.name: line for line in order.guards_line(world) + order.inspectors_line(world)}
check("the state keeps a guards line and an inspectors line", {"guards", "inspectors"} == set(by_name), sorted(by_name))
check("the guards line pays the guards kept at the going wage",
      abs(by_name["guards"].wages - guards * 10.0) < 1e-6 and abs(sum(by_name["guards"].labour.values()) - guards) < 1e-9,
      by_name["guards"])
check("the inspectors line pays the inspectors kept at the going wage",
      abs(by_name["inspectors"].wages - inspectors * 10.0) < 1e-6
      and abs(sum(by_name["inspectors"].labour.values()) - inspectors) < 1e-9, by_name["inspectors"])
check("both are staff the state hires, not a transfer", by_name["guards"].transfer == 0.0 and by_name["inspectors"].transfer == 0.0)

# ---- the game: unpaid staff weaken only the thing they staff, whatever the collection share is --------------------
from sim.engine.agents_port import SimWorld

fed, no_guards, no_inspectors = sim(civ="rome_100ad"), sim(civ="rome_100ad"), sim(civ="rome_100ad")


def leave_unpaid(game, line, share=0.999):
    record = SimWorld(game).government().record
    record.need = dict(record.need, **{line: 1.0})
    record.unfunded = dict(record.unfunded, **{line: share})


leave_unpaid(no_guards, "guards")
leave_unpaid(no_inspectors, "inspectors")
for each in (fed, no_guards, no_inspectors):
    each.household.capital = 1.0e6
    each.state_reach = lambda: 0.5   # the collection share is fixed: only the staff may move the answers below
stolen = {name: each.plunder_founder(0.2, "bandits", True)
          for name, each in (("fed", fed), ("guards", no_guards), ("inspectors", no_inspectors))}
ceiling = {name: each.mine_land_ceiling("iron") for name, each in (("fed", fed), ("guards", no_guards), ("inspectors", no_inspectors))}
check("guards left unpaid raise what thieves take from the founder", stolen["guards"] > stolen["fed"], stolen)
check("inspectors left unpaid lower the mine ceiling", ceiling["inspectors"] < ceiling["fed"], ceiling)
check("guards left unpaid leave the mine ceiling alone", abs(ceiling["guards"] - ceiling["fed"]) < 1e-9, ceiling)
check("inspectors left unpaid leave theft alone", abs(stolen["inspectors"] - stolen["fed"]) < 1e-9, stolen)
