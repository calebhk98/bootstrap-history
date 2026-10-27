"""Paying more to lower a project's chance of failing.

A node declares the `precaution` mechanic naming a `kind` (a pilot plant, a
redundant team). Each kind's share of the bill, share of the founder's hours
and strength of relief are declared once below. A node may override them with
its own `cost_share`, `hours_share` or `relief_per_cost_share` only together
with a `source` saying where the figure comes from. A project started with the
precaution pays both shares through the ordinary bill and hours, and its
failure chance is divided by the relief the money bought.
"""
from typing import Any, Dict, Mapping, Optional

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


def resolve(declared: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    """The node's resolved precaution (label and the three figures) from the parameters it declares, or None."""
    if declared is None:
        return None
    resolved = dict(KINDS[declared["kind"]])
    if declared.get("source"):
        resolved.update({key: declared[key] for key in resolved if key in declared})
    resolved["label"] = declared["kind"].replace("_", " ")
    return resolved


def relief_multiplier(spec: Optional[Mapping[str, Any]], bought: bool) -> float:
    """What the failure chance is multiplied by once the precaution is bought (1.0 when it is not, or none is offered)."""
    if not bought or spec is None:
        return 1.0
    return 1.0 / (1.0 + spec["relief_per_cost_share"] * spec["cost_share"])


def extra_cost(spec: Optional[Mapping[str, Any]], bill: float) -> float:
    return 0.0 if spec is None else bill * spec["cost_share"]


def extra_hours(spec: Optional[Mapping[str, Any]], node_hours: float, rebuild_factor: float) -> float:
    if spec is None:
        return 0.0
    return node_hours * rebuild_factor * spec["hours_share"]


def quote(spec: Optional[Mapping[str, Any]], bill: float, node_hours: float, rebuild_factor: float,
          risk_without: float, risk_with: float) -> Optional[Dict[str, Any]]:
    """What the precaution would cost and buy before the project starts, or None when the node offers none."""
    if spec is None:
        return None
    return {"label": spec["label"],
            "extra_cost": round(extra_cost(spec, bill), 1),
            "extra_founder_hours": round(extra_hours(spec, node_hours, rebuild_factor), 1),
            "chance_of_failure_without": risk_without,
            "chance_of_failure_with": risk_with}
