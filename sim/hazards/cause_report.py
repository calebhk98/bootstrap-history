"""An event's stated causes judged against readings (Complaints/266 item 2).

An event's `causes` is a list of conditions, all of which must hold. Each names a `quantity`, an `op` (one of >, >=, <, <=,
==), a `value` and a `why` giving the historical situation the threshold comes from. `relative_to_start` reads `value` as a
share of the quantity at the start of the run; `node` names the technology of the `state_holds` quantity. With
`causes_effect` "skip" (the default) an event whose causes fail does not happen that year; with "scale" it happens at the
strength the causes hold to, the smallest closeness among them. `causes_not_modelled` lists, in words, historical causes with
no simulated counterpart; they are shown on the divergence screen and judged by nothing. A quantity not yet measured does not
stop an event. The module knows quantity names only, never an event or technology id."""
import operator
from typing import Any, Callable, Dict, List, Mapping, Optional

from sim.refusal import Refusal

from .cause_quantities import QUANTITIES
from .rules import weakened

OPERATORS: Dict[str, Callable[[float, float], bool]] = {
    ">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq}
LOWER_BOUNDS = (">", ">=")
EFFECTS = ("skip", "scale")


def closeness(op: str, value: float, threshold: float) -> float:
    """How near a failed condition is to holding, 0 to 1."""
    if op in LOWER_BOUNDS:
        return max(0.0, min(1.0, value / threshold)) if threshold > 0.0 else 0.0
    if op in ("<", "<="):
        return max(0.0, min(1.0, threshold / value)) if value > 0.0 and threshold > 0.0 else 0.0
    return 0.0


def judge_cause(cause: Dict[str, Any], reading: Optional[float], start_value: Optional[float]) -> Dict[str, Any]:
    """One cause against its reading. A cause relative to the start needs the start value as well; with either one
    unmeasured there is nothing to judge by, so the cause holds."""
    threshold: Optional[float] = float(cause["value"])
    if cause.get("relative_to_start"):
        threshold = None if start_value is None else float(cause["value"]) * float(start_value)
    row = {"quantity": cause["quantity"], "node": cause.get("node"), "op": cause["op"],
           "threshold": None if threshold is None else round(threshold, 4), "value": None, "holds": True,
           "closeness": 1.0, "why": cause.get("why", "")}
    if reading is None or threshold is None:
        return row
    holds = OPERATORS[cause["op"]](float(reading), threshold)
    row.update(value=round(float(reading), 4), holds=holds,
               closeness=1.0 if holds else closeness(cause["op"], float(reading), threshold))
    return row


def report_of(hazard: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """`{checked, conditions, failed, strength}` for an event; `checked` is false when it declares no causes."""
    failed = [row for row in rows if not row["holds"]]
    strength = min((row["closeness"] for row in rows), default=1.0)
    if hazard.get("causes_effect", "skip") == "skip":
        strength = 0.0 if failed else 1.0
    return {"checked": bool(hazard.get("causes")), "conditions": rows, "failed": failed, "strength": strength}


def hazard_after_causes(hazard: Dict[str, Any], report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The event itself when its causes hold or it has none, a weaker copy when it scales, None when it is skipped."""
    if not report["failed"]:
        return hazard
    if report["strength"] <= 0.0:
        return None
    return weakened(hazard, report["strength"])


def cause_problems(hazard: Dict[str, Any], node_ids: Any) -> List[Any]:
    """What is wrong with an event's causes, for `validate`."""
    name = hazard.get("name", "hazard")
    problems: List[Any] = []
    if hazard.get("causes_effect", "skip") not in EFFECTS:
        problems.append("%s: causes_effect must be one of %s" % (name, ", ".join(EFFECTS)))
    unmodelled = hazard.get("causes_not_modelled", [])
    if not isinstance(unmodelled, list) or any(not str(entry).strip() for entry in unmodelled):
        problems.append("%s: causes_not_modelled must be a list of non-empty sentences" % name)
    for cause in hazard.get("causes") or []:
        quantity = QUANTITIES.get(cause.get("quantity"))
        if quantity is None:
            problems.append(Refusal("unknown_quantity", "%s: unknown quantity %r (known: %s)"
                                    % (name, cause.get("quantity"), ", ".join(sorted(QUANTITIES)))))
            continue
        label = "%s / %s" % (name, cause["quantity"])
        if cause.get("op") not in OPERATORS:
            problems.append("%s: operator %r is not one of %s" % (label, cause.get("op"), " ".join(OPERATORS)))
        if not isinstance(cause.get("value"), (int, float)):
            problems.append("%s: value must be a number" % label)
        if not str(cause.get("why", "")).strip():
            problems.append("%s: why is empty; state the historical situation the threshold comes from" % label)
        if quantity.needs_node and cause.get("node") not in node_ids:
            problems.append("%s: node %r is not a technology in the tree" % (label, cause.get("node")))
        if cause.get("relative_to_start") and quantity.start_field is None:
            problems.append("%s: the quantity has no start value to be relative to" % label)
    return problems


def cause_check(civilisations: Mapping[str, Mapping[str, Any]], node_ids: Any) -> List[Any]:
    """`validate`: every civilisation's events' cause problems, each named by its civilisation."""
    return ["%s: %s" % (civ_id, problem)
            for civ_id, civilisation in sorted(civilisations.items())
            for hazard in civilisation.get("hazards") or []
            for problem in cause_problems(hazard, node_ids)]
