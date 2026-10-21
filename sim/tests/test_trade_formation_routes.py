"""Complaint 644, stage 2: migration and bonded purchase in the labour core's year, and who can teach.
Functions called on built inputs, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.labour import trade_formation as formation
from sim.labour.market import aptitude, formation as core_formation
from sim.labour.market.records import Clearing, MarketState, Route, YearInputs, YearReport

HOURS = 2000.0
BANDS = aptitude.band_count()


def clearing(area, trade, wanted_people, hired_people=0.0):
    return Clearing(trade=trade, area=area, wage=1.0, hours_offered=0.0, hours_wanted=(wanted_people + hired_people) * HOURS,
                    hours_hired=hired_people * HOURS, hired_by_employer={}, paid_by_employer={}, average_wage=1.0)


def inputs(routes=None, allowed=frozenset(), for_sale=None):
    return YearInputs(trades={}, bids=(), subsistence_per_worker_year={}, hours_per_worker_year=HOURS,
                      discount_rate=0.05, career_years=40.0, routes=routes or {},
                      bondage_allowed=allowed, bonded_for_sale=for_sale or {})


def people(state, area, trade):
    return sum(state.workers.get(area, {}).get(trade, ()))


def run(state, year_inputs, clearings):
    report = YearReport()
    core_formation.form_trades(state, year_inputs, clearings, report)
    return report


def held_elsewhere():
    """Fitters work in the vale (10 of them, 3 still bid for) and nowhere else; the dale has a vacancy for 8."""
    state = MarketState(workers={"vale": {"fitter": [10.0 / BANDS] * BANDS}})
    clearings = [clearing("vale", "fitter", 0.0, hired_people=3.0), clearing("dale", "fitter", 8.0)]
    return state, clearings


# migration: up to the source's spare hands in a year
state, clearings = held_elsewhere()
report = run(state, inputs(routes={"vale": [Route("dale", 1.0)]}), clearings)
check("an empty trade gains migrants up to the source's spare hands",
      abs(people(state, "dale", "fitter") - 7.0) < 1e-9 and abs(people(state, "vale", "fitter") - 3.0) < 1e-9,
      (people(state, "dale", "fitter"), people(state, "vale", "fitter")))
check("the report names the route", report.formed == {"dale": {"fitter": {"migration": 7.0}}}
      or abs(report.formed["dale"]["fitter"]["migration"] - 7.0) < 1e-9, report.formed)

state, clearings = held_elsewhere()
clearings[1] = clearing("dale", "fitter", 2.0)
run(state, inputs(routes={"vale": [Route("dale", 1.0)]}), clearings)
check("migration stops at what the vacancy wants", abs(people(state, "dale", "fitter") - 2.0) < 1e-9)

state, clearings = held_elsewhere()
run(state, inputs(routes={}), clearings)
check("with no route from the holder the trade stays empty", people(state, "dale", "fitter") == 0.0)

state, clearings = held_elsewhere()
state.workers["dale"] = {"fitter": [0.5] * BANDS}
run(state, inputs(routes={"vale": [Route("dale", 1.0)]}), clearings)
check("a trade that already has people in the area is not formed", abs(people(state, "dale", "fitter") - 0.5 * BANDS) < 1e-9)

# bonded purchase only where the civilisation allows it, at the owners' ask and the buyers' bid (bonded_worth.py)
FLOORS = {"dale": 100.0, "vale": 100.0}


def priced(**changes):
    year_inputs = inputs(**changes)
    year_inputs.ask_floor_per_worker_year = dict(FLOORS)
    return year_inputs


state = MarketState()
report = run(state, priced(allowed=frozenset(), for_sale={"dale": {"fitter": 9.0}}), [clearing("dale", "fitter", 8.0)])
check("an area whose civilisation forbids bondage buys none", people(state, "dale", "fitter") == 0.0 and not report.formed, report.formed)
state = MarketState()
report = run(state, priced(allowed=frozenset({"dale"}), for_sale={"dale": {"fitter": 5.0}}), [clearing("dale", "fitter", 8.0)])
check("where bondage is allowed it buys up to what is for sale",
      abs(people(state, "dale", "fitter") - 5.0) < 1e-9 and abs(report.formed["dale"]["fitter"]["bonded"] - 5.0) < 1e-9, report.formed)
check("the lot is priced: the ask is the trained person's worth where the owner is, no carriage at home",
      len(report.bonded_lots) == 1 and report.bonded_lots[0].origin == "dale" and report.bonded_lots[0].carriage == 0.0
      and report.bonded_lots[0].ask > 0.0, report.bonded_lots)
state = MarketState()
report = run(state, inputs(allowed=frozenset({"dale"}), for_sale={"dale": {"fitter": 5.0}}), [clearing("dale", "fitter", 8.0)])
check("with no wage floor and no practised wage anywhere no price can be named, so none is bought",
      people(state, "dale", "fitter") == 0.0 and not report.bonded_lots, report.bonded_lots)

state, clearings = held_elsewhere()
report = run(state, priced(routes={"vale": [Route("dale", 1.0)]}, allowed=frozenset({"dale"}), for_sale={"dale": {"fitter": 5.0}}), clearings)
check("migration comes before purchase", abs(people(state, "dale", "fitter") - 8.0) < 1e-9 and abs(people(state, "vale", "fitter") - 3.0) < 1e-9
      and abs(report.formed["dale"]["fitter"]["bonded"] - 1.0) < 1e-9, report.formed)

# a trade with some hands but vacancies left buys bonded people too: the slave trade between areas
state = MarketState(workers={"dale": {"fitter": [1.0 / BANDS] * BANDS}})
report = run(state, priced(routes={"vale": [Route("dale", 5.0)]}, allowed=frozenset({"dale", "vale"}),
                           for_sale={"vale": {"fitter": 50.0}}), [clearing("dale", "fitter", 4.0, hired_people=1.0)])
check("a short trade buys bonded people from an area with a route in, carriage paid",
      abs(report.formed["dale"]["fitter"]["bonded"] - 4.0) < 1e-9 and report.bonded_lots[0].origin == "vale"
      and report.bonded_lots[0].carriage == 5.0, report.bonded_lots)

# teachers: knowledge held by any actor
GATING = {"fitter": frozenset({"steam_engine"}), "smith": frozenset({""})}
check("a trade whose knowledge no actor holds has no teacher",
      not formation.teacher_present("fitter", GATING, {"founder": {"other_node"}, "guild": set()}))
check("an actor other than the founder can be the teacher",
      formation.teachers_of("fitter", GATING, {"founder": set(), "guild": {"steam_engine"}}) == ["guild"])
check("the founder can be the teacher", formation.teachers_of("fitter", GATING, {"founder": {"steam_engine"}}) == ["founder"])
check("every holder is named, in id order",
      formation.teachers_of("fitter", GATING, {"zed": {"steam_engine"}, "ada": {"steam_engine"}}) == ["ada", "zed"])
check("a node the society already knows is taught by the society",
      formation.teachers_of("fitter", GATING, {}, baseline={"steam_engine"}) == [formation.SOCIETY])
check("a technique needing no technology is taught by the society", formation.teachers_of("smith", GATING, {}) == [formation.SOCIETY])
check("a demonstrated technique has a holder even when no listed actor does",
      formation.teacher_present("fitter", GATING, {}, demonstrated={"steam_engine"}))
check("a trade no recipe books hours to has no teacher", not formation.teacher_present("scribe", GATING, {"guild": {"steam_engine"}}))

recipes = {"a": {"requires_node": "steam_engine", "labour_hours": {"fitter": 5.0}},
           "b": {"requires_node": None, "labour_hours": {"smith": 5.0}},
           "c": {"labour_hours": {"wright": 5.0}}}
check("gating nodes come from the recipes' requires_node",
      formation.gating_nodes_by_trade(recipes) == {"fitter": frozenset({"steam_engine"}), "smith": frozenset({""})})
