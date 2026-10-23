"""SCENARIO (Complaint 660): in the home game, guards, inspectors and foresters left unpaid weaken only what they staff: theft, the
mine ceiling and the forest ceiling, whatever the collection share is. The rules are in test_state_guards_and_inspectors."""
from .harness import *  # noqa: F401,F403

sim = unopened_sim

from sim.engine.agents_port import SimWorld

fed, no_guards, no_inspectors, no_foresters = (sim(civ="rome_100ad") for _ in range(4))


def leave_unpaid(game, line, share=0.999):
    record = SimWorld(game).government().record
    record.need = dict(record.need, **{line: 1.0})
    record.unfunded = dict(record.unfunded, **{line: share})


leave_unpaid(no_guards, "guards")
leave_unpaid(no_inspectors, "inspectors")
leave_unpaid(no_foresters, "foresters")
for each in (fed, no_guards, no_inspectors, no_foresters):
    each.household.capital = 1.0e6
    each.state_reach = lambda: 0.5   # the collection share is fixed: only the staff may move the answers below
stolen = {name: each.plunder_founder(0.2, "bandits", True)
          for name, each in (("fed", fed), ("guards", no_guards), ("inspectors", no_inspectors))}
ceiling = {name: each.mine_land_ceiling("iron") for name, each in (("fed", fed), ("guards", no_guards), ("inspectors", no_inspectors))}
check("guards left unpaid raise what thieves take from the founder", stolen["guards"] > stolen["fed"], stolen)
check("inspectors left unpaid lower the mine ceiling", ceiling["inspectors"] < ceiling["fed"], ceiling)
check("guards left unpaid leave the mine ceiling alone", abs(ceiling["guards"] - ceiling["fed"]) < 1e-9, ceiling)
check("inspectors left unpaid leave theft alone", abs(stolen["inspectors"] - stolen["fed"]) < 1e-9, stolen)
forest = {name: each.forest_land_ceiling() for name, each in (("fed", fed), ("guards", no_guards), ("foresters", no_foresters))}
check("foresters left unpaid lower the forest ceiling", forest["foresters"] < forest["fed"], forest)
check("guards left unpaid leave the forest ceiling alone", abs(forest["guards"] - forest["fed"]) < 1e-9, forest)
check("foresters left unpaid leave the mine ceiling alone",
      abs(no_foresters.mine_land_ceiling("iron") - ceiling["fed"]) < 1e-9)
