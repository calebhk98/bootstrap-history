"""Complaint 120: money can buy a lower chance of failing, at a stated cost. The precaution's resolution, cost, hours,
relief and quote, each on the projects module holding one declared node (no game). The start is
test_precaution_start."""
from types import SimpleNamespace

from .harness import check, NODES

from sim.projects import precaution_rules
from sim.tests import projects_host

QUICK_TOPIC = True

BILL = 1000.0
HOURS = 200.0
BASE_RISK = 0.4


def _game(mechanics, work_factor=1.0):
    nodes = {"declared": {"ph": HOURS, "mechanics": mechanics}, "plain": {"ph": HOURS, "mechanics": {}}}
    game = projects_host.build(
        tree=nodes, project_cost=lambda node_id: BILL, projects_record=SimpleNamespace(active={}),
        mechanic=lambda name: {node_id: node["mechanics"][name] for node_id, node in nodes.items() if name in node["mechanics"]})
    game.rebuild_work_factor = lambda node_id: work_factor

    def effective_risk(node_id, precaution=False):
        return BASE_RISK * game.precaution_relief(node_id, precaution) if game.precaution_spec(node_id) else BASE_RISK
    game.effective_risk = effective_risk
    return game


PILOT = _game({"precaution": {"kind": "pilot_plant"}})
TEAM = _game({"precaution": {"kind": "redundant_team"}})
KINDS = precaution_rules.KINDS

# --- resolution
resolved = PILOT.precaution_spec("declared")
check("a declared kind resolves to its figures and a label made of its name",
      resolved["label"] == "pilot plant" and resolved["cost_share"] == KINDS["pilot_plant"]["cost_share"], resolved)
check("a node that declares none has none", PILOT.precaution_spec("plain") is None and PILOT.precaution_quote("plain") is None)
unsourced = _game({"precaution": {"kind": "pilot_plant", "cost_share": 0.9}})
check("a figure overridden without a source is ignored",
      unsourced.precaution_spec("declared")["cost_share"] == KINDS["pilot_plant"]["cost_share"])
sourced = _game({"precaution": {"kind": "pilot_plant", "cost_share": 0.9, "source": "a trial report"}})
check("a figure overridden with a source is used",
      sourced.precaution_spec("declared")["cost_share"] == 0.9
      and sourced.precaution_spec("declared")["hours_share"] == KINDS["pilot_plant"]["hours_share"])

# --- cost and hours
check("the extra cost is the bill times the kind's cost share",
      abs(PILOT.precaution_extra_cost("declared", BILL) - BILL * KINDS["pilot_plant"]["cost_share"]) < 1e-9)
check("a node with none adds no cost or hours",
      PILOT.precaution_extra_cost("plain", BILL) == 0.0 and PILOT.precaution_extra_hours("plain") == 0.0)
check("the extra hours are the node's hours times the kind's hours share",
      abs(PILOT.precaution_extra_hours("declared") - HOURS * KINDS["pilot_plant"]["hours_share"]) < 1e-9)
check("rebuilding a lost technology scales the extra hours with the work factor",
      abs(_game({"precaution": {"kind": "redundant_team"}}, work_factor=0.5).precaution_extra_hours("declared")
          - HOURS * 0.5 * KINDS["redundant_team"]["hours_share"]) < 1e-9)
check("the two kinds are different figures", KINDS["pilot_plant"] != KINDS["redundant_team"])

# --- relief
for name, kind in KINDS.items():
    figure = 1.0 / (1.0 + kind["relief_per_cost_share"] * kind["cost_share"])
    check("%s: the relief divides the chance by one plus strength times share spent, and never reaches zero" % name,
          abs(_game({"precaution": {"kind": name}}).precaution_relief("declared", True) - figure) < 1e-12
          and 0.0 < figure < 1.0, figure)
check("a precaution not bought, or not offered, changes nothing",
      PILOT.precaution_relief("declared", False) == 1.0 and PILOT.precaution_relief("plain", True) == 1.0)

# --- the quote
quote = PILOT.precaution_quote("declared")
check("the quote names what is bought", quote["label"] == "pilot plant", quote)
check("the quote shows the cost and the hours",
      quote["extra_cost"] == round(BILL * KINDS["pilot_plant"]["cost_share"], 1)
      and quote["extra_founder_hours"] == round(HOURS * KINDS["pilot_plant"]["hours_share"], 1), quote)
check("the quote shows a lower chance with the lever than without, and the ordinary one without",
      quote["chance_of_failure_with"] < quote["chance_of_failure_without"] == BASE_RISK, quote)
check("the lever never makes the work safe", quote["chance_of_failure_with"] > 0, quote)
check("a project that bought it is reported as having chosen it",
      not PILOT.precaution_chosen("declared")
      and projects_host.build(
          projects_record=SimpleNamespace(active={"declared": {"precaution": True}})).precaution_chosen("declared"))

# --- the data: every declared precaution names a known kind and overrides figures only with a source
check("every declared precaution names a known kind and overrides figures only with a source",
      all(node["mechanics"]["precaution"]["kind"] in KINDS
          and ("source" in node["mechanics"]["precaution"]
               or not {"cost_share", "hours_share", "relief_per_cost_share"} & set(node["mechanics"]["precaution"]))
          for node in NODES.values() if "precaution" in node.get("mechanics", {})))
check("the node of the scenario offers a precaution and its risk is above zero",
      "precaution" in NODES["cap_heat_1600"]["mechanics"] and NODES["cap_heat_1600"]["risk"] > 0)
