"""Complaint 644: the first people of an empty trade. Functions called on built recipes and trades, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.labour import trade_formation as formation

RECIPES = {
    "bar": {"outputs": {"bar": 1}, "inputs": {"ore": 2, "fuel": 2}, "labour_hours": {"smith": 10.0}},
    "gear": {"outputs": {"gear": 1}, "inputs": {"bar": 1, "timber": 1}, "labour_hours": {"smith": 6.0, "wright": 10.0}},
    "wheel": {"outputs": {"wheel": 1}, "inputs": {"timber": 1}, "labour_hours": {"wright": 10.0, "fitter": 6.0}},
    "engine": {"outputs": {"engine": 1}, "inputs": {"bar": 1, "timber": 1}, "labour_hours": {"fitter": 20.0}},
    "grain": {"outputs": {"grain": 1}, "labour_hours": {"farmer": 5.0}},
}
SHARES = formation.task_shares_by_trade(RECIPES)

check("shares of a trade sum to one", all(abs(sum(row.values()) - 1.0) < 1e-9 for row in SHARES.values()), SHARES)
check("a recipe's hours are split over its inputs",
      abs(SHARES["farmer"]["extract:grain"] - 1.0) < 1e-9 and abs(SHARES["smith"]["ore"] - 5.0 / 16.0) < 1e-9, SHARES["smith"])

# distance
check("identical task shares are at distance zero", formation.task_distance(SHARES["smith"], SHARES["smith"]) < 1e-9)
check("distance is symmetric",
      formation.task_distance(SHARES["smith"], SHARES["wright"]) == formation.task_distance(SHARES["wright"], SHARES["smith"]))
check("trades sharing no task are at distance one", formation.task_distance(SHARES["farmer"], SHARES["smith"]) == 1.0)
check("a trade that shares tasks is nearer than one that shares none",
      formation.task_distance(SHARES["fitter"], SHARES["wright"]) < formation.task_distance(SHARES["fitter"], SHARES["farmer"]))

# conversion time
near_years = formation.training_years(6.0, formation.uncovered_share(SHARES["fitter"], SHARES["wright"]))
far_years = formation.training_years(6.0, formation.uncovered_share(SHARES["fitter"], SHARES["farmer"]))
check("a nearer source trade trains faster", near_years < far_years, (near_years, far_years))
check("the nearest source is ranked first",
      formation.nearest_sources("fitter", SHARES, ["farmer", "smith", "wright"])[0][1] in ("wright", "smith"))
check("a fully uncovered trade takes the full apprenticeship", abs(far_years - 6.0) < 1e-9, far_years)
check("a fully covered trade still takes the floor", 0.0 < formation.training_years(6.0, 0.0) < near_years)

COMMON = dict(shares=SHARES, full_years={"fitter": 6.0}, hours_per_worker_year=2000.0)
plan = formation.first_people_plan("fitter", 4.0, migrant_spare={}, source_spare={"wright": 10.0}, teacher_present=False, **COMMON)
check("a trade with no teacher stays empty", plan.empty and plan.routes == [], plan)
plan = formation.first_people_plan("fitter", 4.0, migrant_spare={}, source_spare={}, teacher_present=True, **COMMON)
check("a trade with no source stays empty", plan.empty, plan)

# migration limited to spare hands
spare = formation.spare_people(workers=10.0, hours_wanted=6000.0, hours_per_worker_year=2000.0)
check("an area's spare hands are its workers less those bid for", spare == 7.0, spare)
check("an area bid for beyond its workers has none to spare", formation.spare_people(2.0, 9000.0, 2000.0) == 0.0)
plan = formation.first_people_plan("fitter", 20.0, migrant_spare={"vale": spare, "dale": 2.0}, source_spare={},
                                   teacher_present=False, **COMMON)
check("migration is limited to the source's spare hands",
      plan.people == 9.0 and {route.kind for route in plan.routes} == {"migration"}, plan)

# routes in order, each limited, bonded last
plan = formation.first_people_plan("fitter", 20.0, migrant_spare={"vale": 3.0}, source_spare={"wright": 4.0, "farmer": 5.0},
                                   teacher_present=True, bonded_available=2.0, **COMMON)
routes = [(route.kind, route.source, route.people) for route in plan.routes]
check("migration first, then the nearer trade, then the further, then the bonded",
      routes == [("migration", "vale", 3.0), ("conversion", "wright", 4.0), ("conversion", "farmer", 5.0),
                 ("bonded", "bonded market", 2.0)], routes)
check("conversion from the nearer trade is quicker", plan.routes[1].years < plan.routes[2].years, plan.routes)
check("the teacher's hours follow the training time", plan.routes[1].teacher_hours < plan.routes[2].teacher_hours * 4.0 / 5.0)
check("no bonded market, none bought",
      not any(route.kind == "bonded" for route in formation.first_people_plan(
          "fitter", 20.0, migrant_spare={}, source_spare={}, teacher_present=True, bonded_available=0.0, **COMMON).routes))
check("the plan never exceeds what was wanted",
      formation.first_people_plan("fitter", 1.0, migrant_spare={"vale": 5.0}, source_spare={"wright": 3.0},
                                  teacher_present=True, **COMMON).people == 1.0)

# derived from the shipped recipes, not typed
SHIPPED = formation.shipped_task_shares()
check("the shipped recipes describe the trades that work in them", "smith" in SHIPPED and "machinist" in SHIPPED)
