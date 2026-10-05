"""Paying more to lower a project's chance of failing.

A node declares the `precaution` mechanic naming a `kind` (a pilot plant, a
redundant team). Each kind's share of the bill, share of the founder's hours
and strength of relief are declared once below. A node may override them with
its own `cost_share`, `hours_share` or `relief_per_cost_share` only together
with a `source` saying where the figure comes from. A project started with the
precaution pays both shares through the ordinary bill and hours, and its
failure chance is divided by the relief the money bought.
"""
from sim.constants import declare

_NO_SOURCE_WHY = ("The sim does not yet model which failure causes this "
                  "precaution would expose, so the figure is a placeholder, "
                  "not measured.")

PILOT_PLANT_COST_SHARE = declare(
    "PILOT_PLANT_COST_SHARE", 0.15, kind="temporary_heuristic",
    unit="fraction of the project bill added", source=None, confidence="D",
    why="A pilot plant is built and run before the full-scale work, adding "
        "this share of the bill. " + _NO_SOURCE_WHY)
PILOT_PLANT_HOURS_SHARE = declare(
    "PILOT_PLANT_HOURS_SHARE", 0.1, kind="temporary_heuristic",
    unit="fraction of the founder's project hours added", source=None, confidence="D",
    why="Supervising the pilot run takes this share of the project's "
        "founder-hours again. " + _NO_SOURCE_WHY)
PILOT_PLANT_RELIEF = declare(
    "PILOT_PLANT_RELIEF", 4.0, kind="temporary_heuristic",
    unit="risk-reduction strength per unit of the bill spent again",
    source=None, confidence="D",
    why="The failure chance is divided by one plus this strength times the "
        "bill share spent, so spending more helps with diminishing returns "
        "and never reaches zero. " + _NO_SOURCE_WHY)
REDUNDANT_TEAM_COST_SHARE = declare(
    "REDUNDANT_TEAM_COST_SHARE", 0.1, kind="temporary_heuristic",
    unit="fraction of the project bill added", source=None, confidence="D",
    why="A second team works the problem in parallel, adding this share of "
        "the bill. " + _NO_SOURCE_WHY)
REDUNDANT_TEAM_HOURS_SHARE = declare(
    "REDUNDANT_TEAM_HOURS_SHARE", 0.25, kind="temporary_heuristic",
    unit="fraction of the founder's project hours added", source=None, confidence="D",
    why="Directing two teams takes this share of the project's "
        "founder-hours again. " + _NO_SOURCE_WHY)
REDUNDANT_TEAM_RELIEF = declare(
    "REDUNDANT_TEAM_RELIEF", 4.0, kind="temporary_heuristic",
    unit="risk-reduction strength per unit of the bill spent again",
    source=None, confidence="D",
    why="As for the pilot plant: the failure chance is divided by one plus "
        "this strength times the bill share spent. " + _NO_SOURCE_WHY)

KINDS = {
    "pilot_plant": {"cost_share": PILOT_PLANT_COST_SHARE,
                    "hours_share": PILOT_PLANT_HOURS_SHARE,
                    "relief_per_cost_share": PILOT_PLANT_RELIEF},
    "redundant_team": {"cost_share": REDUNDANT_TEAM_COST_SHARE,
                       "hours_share": REDUNDANT_TEAM_HOURS_SHARE,
                       "relief_per_cost_share": REDUNDANT_TEAM_RELIEF},
}


def spec(sim, node_id):
    """The node's resolved precaution (label and the three figures), or None."""
    declared = sim.mechanic(node_id, "precaution")
    if declared is None:
        return None
    resolved = dict(KINDS[declared["kind"]])
    if declared.get("source"):
        resolved.update({key: declared[key] for key in resolved if key in declared})
    resolved["label"] = declared["kind"].replace("_", " ")
    return resolved


def chosen(sim, node_id):
    """True when the running project for this node bought the precaution."""
    return bool((sim.state.projects.active.get(node_id) or {}).get("precaution"))


def relief_multiplier(sim, node_id, bought):
    declared = spec(sim, node_id)
    if not bought or declared is None:
        return 1.0
    return 1.0 / (1.0 + declared["relief_per_cost_share"] * declared["cost_share"])


def extra_cost(sim, node_id, bill):
    declared = spec(sim, node_id)
    return 0.0 if declared is None else bill * declared["cost_share"]


def extra_hours(sim, node_id):
    declared = spec(sim, node_id)
    if declared is None:
        return 0.0
    return sim.nodes[node_id]["ph"] * sim.rebuild_work_factor(node_id) * declared["hours_share"]


def quote(sim, node_id):
    """What the precaution would cost and buy before the project starts,
    or None when the node offers none."""
    declared = spec(sim, node_id)
    if declared is None:
        return None
    return {"label": declared["label"],
            "extra_cost": round(extra_cost(sim, node_id, sim.project_cost(node_id)), 1),
            "extra_founder_hours": round(extra_hours(sim, node_id), 1),
            "chance_of_failure_without": sim.effective_risk(node_id, precaution=False),
            "chance_of_failure_with": sim.effective_risk(node_id, precaution=True)}
