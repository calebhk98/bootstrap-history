"""Quantities events can state causes from beyond the first set, and the shipped events that use them (Complaints/266)."""

QUICK_TOPIC = True

import json
import os
from types import SimpleNamespace

from .harness import check

from sim.engine import event_causes
from sim.engine.tree_source import load_base_tree

CIVILISATIONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "civilizations")


def stratum(members, welfare, share, propertied=False, bonded=False, measured=True):
	plan = {"share": share, "property_share": 0.3 if propertied else 0.0, "bonded": bonded}
	return SimpleNamespace(record=SimpleNamespace(
		country=None, exited_year=None, members=members, welfare=welfare,
		welfare_reference=welfare if measured else 0.0, plan=plan))


def fake_sim(strata=(), nutrition=None, coin_metal_kept=1.0):
	flows = None if nutrition is None else SimpleNamespace(nutrition_ratio=nutrition)
	record = SimpleNamespace(need={"army": 1.0}, unfunded={}, coin_metal_kept=coin_metal_kept)
	return SimpleNamespace(
		_last_demographic_step=flows, population=SimpleNamespace(total=1000.0),
		actors=SimpleNamespace(of_kind=lambda kind: list(strata) if kind == "stratum" else []),
		state_treasury=lambda: SimpleNamespace(record=record),
		civ={}, start_civ={}, cfg={"start_year": 100}, year=120)


def cause(quantity, op, value):
	return {"quantity": quantity, "op": op, "value": value, "why": "fixture reasoning"}


def read(name, sim):
	return event_causes.QUANTITIES[name].read(sim)


check("the new quantities are known", all(name in event_causes.QUANTITIES for name in (
	"food_supply_ratio", "lowest_stratum_welfare", "stratum_welfare_spread", "coin_metal_kept",
	"elite_share_vs_opening")))

# food supply
check("food supply reads last year's nutrition ratio", read("food_supply_ratio", fake_sim(nutrition=0.8)) == 0.8)
check("food supply is unknown before the first year", read("food_supply_ratio", fake_sim()) is None)
famine = {"name": "Famine", "causes": [cause("food_supply_ratio", "<", 1.1)]}
check("an unknown reading lets the event stand (nothing to judge by)",
	event_causes.effective_hazard(fake_sim(), famine)[0] is famine)
check("a well fed society has no famine", event_causes.effective_hazard(fake_sim(nutrition=1.5), famine)[0] is None)
check("a thinly fed one has it", event_causes.effective_hazard(fake_sim(nutrition=0.9), famine)[0] is famine)

# strata
strata = [stratum(10.0, 2.0, 0.01, propertied=True), stratum(900.0, 0.8, 0.9), stratum(90.0, 0.4, 0.09),
		  stratum(100.0, 0.1, 0.1, bonded=True)]
check("the poorest body is the lowest welfare among free, measured strata",
	read("lowest_stratum_welfare", fake_sim(strata)) == 0.4)
check("the spread is best over worst welfare", abs(read("stratum_welfare_spread", fake_sim(strata)) - 5.0) < 1e-9)
check("strata not yet measured give no reading",
	read("lowest_stratum_welfare", fake_sim([stratum(5.0, 0.0, 1.0, measured=False)])) is None)
check("no strata give no reading", read("stratum_welfare_spread", fake_sim()) is None)

# elite numbers against the opening split
grown = [stratum(20.0, 1.0, 0.01, propertied=True), stratum(980.0, 1.0, 0.99)]
check("elite numbers over the opening share are 1 when unchanged",
	abs(read("elite_share_vs_opening", fake_sim([stratum(10.0, 1.0, 0.01, propertied=True),
												stratum(990.0, 1.0, 0.99)])) - 1.0) < 1e-9)
check("and 2 when the elite has doubled its share", abs(read("elite_share_vs_opening", fake_sim(grown)) - 2.0) < 1e-9)

# coin
check("an undebased coin keeps all its metal", read("coin_metal_kept", fake_sim()) == 1.0)
solidus = {"name": "Restoration", "causes": [cause("coin_metal_kept", "<", 1.0)]}
check("there is nothing to restore when the coin was never cut",
	event_causes.effective_hazard(fake_sim(), solidus)[0] is None)
check("a cut coin can be restored", event_causes.effective_hazard(fake_sim(coin_metal_kept=0.6), solidus)[0] is solidus)

# causes the model cannot check are listed, not silently dropped
check("a not-modelled list of words is accepted",
	event_causes.cause_problems({"name": "x", "causes_not_modelled": ["court legitimacy"]}, set()) == [])
check("an empty entry in it is rejected", any("causes_not_modelled" in problem for problem in event_causes.cause_problems(
	{"name": "x", "causes_not_modelled": [" "]}, set())))
check("a non-list is rejected", any("causes_not_modelled" in problem for problem in event_causes.cause_problems(
	{"name": "x", "causes_not_modelled": "legitimacy"}, set())))

# the shipped data: every dated event the complaint named states causes, or says what it cannot check
STATES_CAUSES = {
	"rome_100ad.json": ["The solidus and the end of the debasement", "Christianisation of the empire",
						"Justinian's Gothic War", "The Arab conquests close the Mediterranean",
						"Ostrogothic Italy under Theodoric", "The Carolingian renaissance",
						"Third century crisis"],
	"han_china_100ad.json": ["The regency cycle and the Partisan Prohibitions", "Yellow Turban rebellion",
							 "Three Kingdoms fragmentation", "Jin reunification and the Taikang peace",
							 "War of the Eight Princes", "Sui reunification", "Tang founding and the Zhenguan peace",
							 "Empress Wu's Zhou interregnum", "The An Lushan rebellion"],
	"england_1300.json": ["Great Famine", "Hundred Years War", "Wars of the Roses", "The dearth of the 1590s",
						  "Civil War and Interregnum", "The great frost and the dearth of 1740"],
	"mexica_1500.json": ["Spanish invasion", "The Revolution", "The wars of independence"],
	"norse_900ad.json": ["Norwegian civil war era", "Christianisation and political consolidation"],
}
tree_nodes = {node["id"] for node in load_base_tree()["nodes"]}
problems = []
missing = []
for filename, names in STATES_CAUSES.items():
	with open(os.path.join(CIVILISATIONS, filename), encoding="utf-8") as handle:
		events = {event["name"]: event for event in json.load(handle)["hazards"]}
	for name in names:
		event = events.get(name)
		if event is None or not (event.get("causes") or event.get("causes_not_modelled")):
			missing.append("%s / %s" % (filename, name))
	for event in events.values():
		problems += event_causes.cause_problems(event, tree_nodes)
check("the named events state causes or what they cannot check", missing == [], str(missing))
check("every shipped event's causes are well formed", problems == [], str(problems))
