"""Complaint 491: the materials a year of research consumes come from the actor's own stores, then from a bid at the market."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import research_materials
from sim.engine import validate_action_results


def price(material, tonnes):
	return None if material == "unsold" else 10.0 * tonnes


def run(stores, needs):
	bids = []
	covered = research_materials.cover_year(stores, needs, price, lambda material, tonnes, budget: bids.append((material, tonnes, budget)))
	return covered, bids


stores = {"copper": 3.0}
covered, bids = run(stores, {"copper": 5.0})
check("stock is drawn first and only the shortfall is bid for", bids == [("copper", 2.0, 20.0)] and stores["copper"] == 0.0, bids)
check("the money covered is the drawn stock plus the bid", abs(covered - 50.0) < 1e-9, covered)

stores = {"copper": 9.0}
covered, bids = run(stores, {"copper": 5.0})
check("held stock that covers the year buys nothing", bids == [] and abs(stores["copper"] - 4.0) < 1e-9, (bids, stores))

stores = {}
covered, bids = run(stores, {"unsold": 2.0})
check("a shortfall nobody sells is left owed, not covered", covered == 0.0 and bids == [], (covered, bids))

check("nothing needed covers nothing", run({"copper": 1.0}, {}) == (0.0, []))

nodes = {"voyage": {"returns": {"sample": ["vine"]}}, "rubber": {"samples": ["sample:vine"]}, "wish": {"samples": ["sample:none"]}}
problems = validate_action_results.check_action_results(nodes, [])
check("a sample some action returns is accepted, one nothing returns is refused", len(problems) == 1 and "sample:none" in problems[0], problems)

from sim.agents import imitation
from .test_research_every_actor import ResearchWorld, actors


def year_of_work(name, stock):
	world = ResearchWorld()
	world.prices["copper"] = 10.0
	world.research_tonnes["tech"] = {"copper": 4.0}
	actor = actors()[name]
	actor.record.stores.update(stock)
	work = {"hours": {}, "money": 100.0, "labour_cost": 0.0, "years": 2, "progress": 0.0, "started": 0, "stalled": 0.0}
	imitation.work_year(actor, "tech", work, world)
	return actor, world


firm, world = year_of_work("firm", {})
check("a firm bids for the year's materials as goods", world.purchases == [("firm:1", "copper", 2.0)], world.purchases)
check("and pays only the rest of the year's money through the project", abs(5000.0 - firm.money - 30.0) < 1e-6, firm.money)
firm, world = year_of_work("firm", {"copper": 10.0})
check("a firm holding the stock buys nothing and draws it down", world.purchases == [] and abs(firm.record.stores["copper"] - 8.0) < 1e-9)
state, world = year_of_work("state", {})
check("a state that does not keep purchases pays the whole year through the project", world.purchases == [] and abs(5000.0 - state.money - 50.0) < 1e-6, state.money)
