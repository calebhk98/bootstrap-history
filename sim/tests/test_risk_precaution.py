"""Complaint 120: money can buy a lower chance of failing, at a stated cost. The precaution's resolution, cost, hours,
relief and quote, each on a stand-in game holding one declared node (no game). The start through the dispatcher is
test_risk_precaution_scenario."""
from types import SimpleNamespace

from .harness import check, NODES

from sim.engine import projects_precaution as rules

QUICK_TOPIC = True

BILL = 1000.0
HOURS = 200.0
BASE_RISK = 0.4


def _game(mechanics, work_factor=1.0):
    nodes = {"declared": {"ph": HOURS, "mechanics": mechanics}, "plain": {"ph": HOURS, "mechanics": {}}}

    def effective_risk(node_id, precaution=False):
        declared = rules.spec(game, node_id)
        return BASE_RISK * rules.relief_multiplier(game, node_id, precaution) if declared else BASE_RISK

    game = SimpleNamespace(
        nodes=nodes, project_cost=lambda node_id: BILL, rebuild_work_factor=lambda node_id: work_factor,
        mechanic=lambda node_id, name: nodes[node_id]["mechanics"].get(name), effective_risk=effective_risk,
        state=SimpleNamespace(projects=SimpleNamespace(active={})))
    return game


PILOT = _game({"precaution": {"kind": "pilot_plant"}})
TEAM = _game({"precaution": {"kind": "redundant_team"}})
KINDS = rules.KINDS

# --- resolution
resolved = rules.spec(PILOT, "declared")
check("a declared kind resolves to its figures and a label made of its name",
      resolved["label"] == "pilot plant" and resolved["cost_share"] == KINDS["pilot_plant"]["cost_share"], resolved)
check("a node that declares none has none", rules.spec(PILOT, "plain") is None and rules.quote(PILOT, "plain") is None)
unsourced = _game({"precaution": {"kind": "pilot_plant", "cost_share": 0.9}})
check("a figure overridden without a source is ignored",
      rules.spec(unsourced, "declared")["cost_share"] == KINDS["pilot_plant"]["cost_share"])
sourced = _game({"precaution": {"kind": "pilot_plant", "cost_share": 0.9, "source": "a trial report"}})
check("a figure overridden with a source is used",
      rules.spec(sourced, "declared")["cost_share"] == 0.9
      and rules.spec(sourced, "declared")["hours_share"] == KINDS["pilot_plant"]["hours_share"])

# --- cost and hours
check("the extra cost is the bill times the kind's cost share",
      abs(rules.extra_cost(PILOT, "declared", BILL) - BILL * KINDS["pilot_plant"]["cost_share"]) < 1e-9)
check("a node with none adds no cost or hours",
      rules.extra_cost(PILOT, "plain", BILL) == 0.0 and rules.extra_hours(PILOT, "plain") == 0.0)
check("the extra hours are the node's hours times the kind's hours share",
      abs(rules.extra_hours(PILOT, "declared") - HOURS * KINDS["pilot_plant"]["hours_share"]) < 1e-9)
check("rebuilding a lost technology scales the extra hours with the work factor",
      abs(rules.extra_hours(_game({"precaution": {"kind": "redundant_team"}}, work_factor=0.5), "declared")
          - HOURS * 0.5 * KINDS["redundant_team"]["hours_share"]) < 1e-9)
check("the two kinds are different figures", KINDS["pilot_plant"] != KINDS["redundant_team"])

# --- relief
for name, kind in KINDS.items():
    figure = 1.0 / (1.0 + kind["relief_per_cost_share"] * kind["cost_share"])
    check("%s: the relief divides the chance by one plus strength times share spent, and never reaches zero" % name,
          abs(rules.relief_multiplier(_game({"precaution": {"kind": name}}), "declared", True) - figure) < 1e-12
          and 0.0 < figure < 1.0, figure)
check("a precaution not bought, or not offered, changes nothing",
      rules.relief_multiplier(PILOT, "declared", False) == 1.0 and rules.relief_multiplier(PILOT, "plain", True) == 1.0)

# --- the quote
quote = rules.quote(PILOT, "declared")
check("the quote names what is bought", quote["label"] == "pilot plant", quote)
check("the quote shows the cost and the hours",
      quote["extra_cost"] == round(BILL * KINDS["pilot_plant"]["cost_share"], 1)
      and quote["extra_founder_hours"] == round(HOURS * KINDS["pilot_plant"]["hours_share"], 1), quote)
check("the quote shows a lower chance with the lever than without, and the ordinary one without",
      quote["chance_of_failure_with"] < quote["chance_of_failure_without"] == BASE_RISK, quote)
check("the lever never makes the work safe", quote["chance_of_failure_with"] > 0, quote)
check("a project that bought it is reported as having chosen it",
      not rules.chosen(PILOT, "declared")
      and rules.chosen(SimpleNamespace(state=SimpleNamespace(projects=SimpleNamespace(
          active={"declared": {"precaution": True}}))), "declared"))

# --- the data: every declared precaution names a known kind and overrides figures only with a source
check("every declared precaution names a known kind and overrides figures only with a source",
      all(node["mechanics"]["precaution"]["kind"] in KINDS
          and ("source" in node["mechanics"]["precaution"]
               or not {"cost_share", "hours_share", "relief_per_cost_share"} & set(node["mechanics"]["precaution"]))
          for node in NODES.values() if "precaution" in node.get("mechanics", {})))
check("the node of the scenario offers a precaution and its risk is above zero",
      "precaution" in NODES["cap_heat_1600"]["mechanics"] and NODES["cap_heat_1600"]["risk"] > 0)
