"""Paying more to lower a project's chance of failing.

A node declares the `precaution` mechanic: the `label` of what is bought
(a pilot plant, a redundant team), the `cost_share` of the bill added on top
and the `hours_share` of the founder's hours added. A project started with the
precaution pays both, through the ordinary bill and hours, and its failure
chance is divided by the relief the money bought.
"""
from sim.constants import declare

RELIEF_PER_COST_SHARE = declare(
    "RELIEF_PER_COST_SHARE", 4.0, kind="temporary_heuristic",
    unit="added risk-reduction strength per unit of the bill spent again",
    source=None, confidence="D",
    why="The failure chance is divided by one plus this strength times the "
        "share of the bill spent on a pilot or a redundant team, so spending "
        "more always helps but with diminishing returns and never reaches "
        "zero. The sim does not yet model which failure causes a pilot run "
        "would expose, so the strength is a placeholder, not measured.")


def spec(sim, node_id):
    return sim.mechanic(node_id, "precaution")


def chosen(sim, node_id):
    """True when the running project for this node bought the precaution."""
    return bool((sim.state.projects.active.get(node_id) or {}).get("precaution"))


def relief_multiplier(sim, node_id, bought):
    declared = spec(sim, node_id)
    if not bought or declared is None:
        return 1.0
    return 1.0 / (1.0 + RELIEF_PER_COST_SHARE * declared["cost_share"])


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
