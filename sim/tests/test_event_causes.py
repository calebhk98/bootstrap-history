"""Dated events state their causes in data and are skipped, weakened or kept by them (Complaints/266 item 2)."""

QUICK_TOPIC = True

import json
import os
from types import SimpleNamespace

from .harness import check
from sim.refusal import cause_of

from sim.hazards import cause_report
from sim.content.tree_source import load_base_tree
from sim.ui.proto.screen_divergence import _dated_events
from sim.tests.ui_stand_in import Game
from sim.tests import hazards_host

CIVILISATIONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "civilizations")


def fake_sim(population=1000.0, start_population=1000.0, funded=True, held=()):
	"""The hazards module over written-out facts: the society's people, the state's books, what the state holds."""
	held = set(held)
	return hazards_host.build(
		population_total=population, civilisation={"id": "rome", "hazards": []},
		opening_civilisation={"population": start_population, "literacy_general": 0.1},
		state_budget_figures={"need": 100.0, "unfunded": 0.0 if funded else 40.0, "coin_metal_kept": 1.0},
		state_knows=lambda node: node in held)


def cause(quantity, op, value, **extra):
	return dict({"quantity": quantity, "op": op, "value": value, "why": "fixture reasoning"}, **extra)


# a cause that holds lets the event fire unchanged
hazard = {"name": "Fixture plague", "years": [110, 130], "staff_loss": 0.2,
          "causes": [cause("population", ">=", 500.0)]}
kept, report = fake_sim().effective_hazard(hazard)
check("an event whose cause holds fires as written", kept is hazard and report["checked"])
check("the report lists the cause with its value", report["conditions"][0]["value"] == 1000.0)

# a cause that fails skips the event and names the failed cause
kept, report = fake_sim(population=100.0).effective_hazard(hazard)
check("an event whose cause fails is skipped", kept is None)
check("the report names the failed cause", [row["quantity"] for row in report["failed"]] == ["population"])

# a threshold taken relative to the start value
relative = {"name": "Relative", "years": [110, 130], "staff_loss": 0.2,
            "causes": [cause("population", ">=", 0.5, relative_to_start=True)]}
check("a relative threshold holds above its share of the start value",
      fake_sim(population=600.0).effective_hazard(relative)[0] is relative)
check("a relative threshold fails below its share of the start value",
      fake_sim(population=400.0).effective_hazard(relative)[0] is None)

# the state's funding and the technology it holds
fiscal = {"name": "Fiscal", "years": [110, 130], "output_factor": 0.6,
          "causes": [cause("state_funded_share", "<", 1.0)]}
check("a fully funded state has no fiscal crisis",
      fake_sim(funded=True).effective_hazard(fiscal)[0] is None)
check("a state short of money has one",
      fake_sim(funded=False).effective_hazard(fiscal)[0] is fiscal)
invasion = {"name": "Invasion", "years": [110, 130], "sack_chance": 0.5,
            "causes": [cause("state_holds", "==", 0.0, node="fixture_weapon")]}
check("the invasion is skipped when the state holds the weapon",
      fake_sim(held={"fixture_weapon"}).effective_hazard(invasion)[0] is None)
check("the invasion fires when it does not",
      fake_sim().effective_hazard(invasion)[0] is invasion)

# an event with a strength is scaled by how far its causes hold
scaled = {"name": "Scaled", "years": [110, 130], "sack_chance": 0.4, "output_factor": 0.5,
          "causes_effect": "scale", "causes": [cause("population", ">=", 1000.0)]}
weakened, report = fake_sim(population=500.0).effective_hazard(scaled)
check("a scaled event keeps firing, weaker", weakened is not scaled and abs(weakened["sack_chance"] - 0.2) < 1e-9)
check("the output shortfall shrinks by the same share", abs(weakened["output_factor"] - 0.75) < 1e-9)
check("the report carries the strength", abs(report["strength"] - 0.5) < 1e-9)
check("the original hazard is untouched", scaled["sack_chance"] == 0.4)

# an event with no causes is not checked
plain = {"name": "Plain", "years": [110, 130], "sack_chance": 0.1}
kept, report = fake_sim().effective_hazard(plain)
check("an event with no causes fires and says it was not checked", kept is plain and not report["checked"])

# the divergence screen reports the evaluation
reporter = fake_sim(population=100.0)
screen_sim = Game(civ={"hazards": [hazard, plain]}, cfg={"start_year": 100}, year=120, fog=False,
                  event_cause_report=reporter.event_cause_report)
rows = {row["name"]: row for row in _dated_events(screen_sim)}
check("the divergence screen says the causes were checked", rows["Fixture plague"]["causes_checked"] is True)
check("and which cause failed", rows["Fixture plague"]["failed_causes"][0]["quantity"] == "population")
check("an event without causes stays unchecked", rows["Plain"]["causes_checked"] is False)

# validation
nodes = {"fixture_weapon"}
check("a well formed cause list has no problems", cause_report.cause_problems(hazard, nodes) == [])
check("an unknown quantity is rejected",
      any(cause_of(problem) == "unknown_quantity" for problem in
          cause_report.cause_problems({"name": "x", "causes": [cause("moon_phase", ">", 1)]}, nodes)))
check("an unknown operator is rejected",
      any("operator" in problem for problem in
          cause_report.cause_problems({"name": "x", "causes": [cause("population", "~", 1)]}, nodes)))
check("a cause with no reasoning is rejected",
      any("why" in problem for problem in cause_report.cause_problems(
          {"name": "x", "causes": [{"quantity": "population", "op": ">", "value": 1}]}, nodes)))
check("a technology cause naming no such node is rejected",
      any("node" in problem for problem in cause_report.cause_problems(
          {"name": "x", "causes": [cause("state_holds", "==", 0.0, node="ghost")]}, nodes)))
check("a relative threshold on a quantity with no start value is rejected",
      any("start" in problem for problem in cause_report.cause_problems(
          {"name": "x", "causes": [cause("state_funded_share", "<", 1.0, relative_to_start=True)]}, nodes)))

# the shipped data
tree_nodes = {node["id"] for node in load_base_tree()["nodes"]}
problems = []
carrying = 0
for filename in sorted(os.listdir(CIVILISATIONS)):
	if filename.endswith(".json") and not filename.startswith("_"):
		with open(os.path.join(CIVILISATIONS, filename), encoding="utf-8") as handle:
			for event in json.load(handle).get("hazards", []):
				problems += cause_report.cause_problems(event, tree_nodes)
				carrying += bool(event.get("causes"))
check("every shipped event's causes are well formed", problems == [], str(problems))
check("shipped events carry causes", carrying > 0)

# the yearly driver: a skipped event is told once, in the log, with the failed cause
from sim.reporting.api import RecordEvent
from sim.tests import module_harness

module = hazards_host.build(population_total=100.0, opening_civilisation={"population": 1000.0})
told = lambda: [command for command in module_harness.sent(module) if isinstance(command, RecordEvent)]
check("the driver drops an event whose cause fails", module.apply_event_causes(hazard, 110, 110) is None)
module.apply_event_causes(hazard, 110, 110)
check("and says why once", len(told()) == 1 and "fixture reasoning" in told()[0].text)
check("the driver passes an event that states no causes", module.apply_event_causes(plain, 110, 110) is plain)

# validate reports a bad cause from any civilisation
errors = cause_report.cause_check(
	{"somewhere": {"hazards": [{"name": "Bad", "causes": [cause("moon_phase", ">", 1)]}]}}, nodes)
check("validate names the civilisation and the unknown quantity",
      len(errors) == 1 and errors[0].startswith("somewhere: Bad") and "unknown quantity" in errors[0], str(errors))
