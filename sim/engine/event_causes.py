"""Causes of dated events (Complaints/266 item 2): conditions a civilisation's data states for an event,
checked against quantities the engine already exposes.

An event's `causes` is a list of conditions, all of which must hold. Each names a `quantity`, an `op`
(one of >, >=, <, <=, ==), a `value` and a `why` giving the historical situation the threshold comes from.
`relative_to_start` reads `value` as a share of the quantity at the start of the run; `node` names the
technology of the `state_holds` quantity. With `causes_effect` "skip" (the default) an event whose causes
fail does not happen that year; with "scale" it happens at the strength the causes hold to, the smallest
closeness among them. The engine knows quantity names only, never an event or technology id.
"""
import operator
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

OPERATORS: Dict[str, Callable[[float, float], bool]] = {
    ">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq}
LOWER_BOUNDS = (">", ">=")
EFFECTS = ("skip", "scale")
# hazard fields a weakened event shrinks, and how
SCALED_FIELDS = ("sack_chance", "staff_loss", "real_erosion")


class Quantity(NamedTuple):
    read: Callable[..., float]
    start_field: Optional[str] = None     # civilisation field holding the start value, when there is one
    needs_node: bool = False
    meaning: str = ""


def _world(sim: Any) -> Any:
    from sim.engine.agents_port import SimWorld
    return SimWorld(sim)


def _held_tiles(sim: Any) -> Tuple[List[str], List[str]]:
    from sim.geography.api import tiles_held
    return tiles_held(sim.civ, sim.world_map), tiles_held(sim.start_civ, sim.world_map)


def _funded_share(sim: Any, node: Optional[str] = None) -> float:
    record = sim.state_treasury().record
    need = sum(record.need.values())
    return 1.0 if need <= 0.0 else max(0.0, 1.0 - sum(record.unfunded.values()) / need)


def _army_share_of_wanted(sim: Any, node: Optional[str] = None) -> float:
    world = _world(sim)
    wanted = world.army_wanted()
    return 1.0 if wanted <= 0.0 else world.soldiers_under_arms() / wanted


def _state_holds(sim: Any, node: Optional[str] = None) -> float:
    return 1.0 if sim.state_treasury().knows(node, _world(sim)) else 0.0


def _territory_share(sim: Any, node: Optional[str] = None) -> float:
    now, start = _held_tiles(sim)
    return 1.0 if not start else len(set(now) & set(start)) / len(start)


def _output_hours_per_head(sim: Any, node: Optional[str] = None) -> float:
    people = sim.population.total
    return 0.0 if people <= 0.0 else sim.real_output_hours() / people


QUANTITIES: Dict[str, Quantity] = {
    "population": Quantity(lambda sim, node=None: float(sim.population.total), "population",
                           meaning="people in the society"),
    "output_hours_per_head": Quantity(_output_hours_per_head,
                                      meaning="hours of real output a year per person"),
    "state_funded_share": Quantity(_funded_share,
                                   meaning="share of what the state needs that its revenue covers"),
    "army_share_of_wanted": Quantity(_army_share_of_wanted,
                                     meaning="soldiers kept over the force the state's threat calls for"),
    "literacy_general": Quantity(lambda sim, node=None: float(sim.civ.get("literacy_general", 0.0)),
                                 "literacy_general", meaning="general literacy"),
    "literacy_elite": Quantity(lambda sim, node=None: float(sim.civ.get("literacy_elite", 0.0)),
                               "literacy_elite", meaning="elite literacy"),
    "state_holds": Quantity(_state_holds, needs_node=True, meaning="1 when the state holds the technology `node`, else 0"),
    "territory_share_of_start": Quantity(_territory_share,
                                         meaning="share of the tiles held at the start still held"),
}


def _closeness(op: str, value: float, threshold: float) -> float:
    """How near a failed condition is to holding, 0 to 1."""
    if op in LOWER_BOUNDS:
        return max(0.0, min(1.0, value / threshold)) if threshold > 0.0 else 0.0
    if op in ("<", "<="):
        return max(0.0, min(1.0, threshold / value)) if value > 0.0 and threshold > 0.0 else 0.0
    return 0.0


def _threshold(sim: Any, cause: Dict[str, Any], quantity: Quantity) -> float:
    value = float(cause["value"])
    if not cause.get("relative_to_start"):
        return value
    return value * float((sim.start_civ or {}).get(quantity.start_field, 0.0))


def evaluate_cause(sim: Any, cause: Dict[str, Any]) -> Dict[str, Any]:
    quantity = QUANTITIES[cause["quantity"]]
    value = float(quantity.read(sim, cause.get("node")))
    threshold = _threshold(sim, cause, quantity)
    holds = OPERATORS[cause["op"]](value, threshold)
    return {"quantity": cause["quantity"], "node": cause.get("node"), "op": cause["op"],
            "threshold": round(threshold, 4), "value": round(value, 4), "holds": holds,
            "closeness": 1.0 if holds else _closeness(cause["op"], value, threshold),
            "why": cause.get("why", "")}


def evaluate_causes(sim: Any, hazard: Dict[str, Any]) -> Dict[str, Any]:
    """`{checked, conditions, failed, strength}` for an event; `checked` is false when it declares no causes."""
    causes = hazard.get("causes") or []
    rows = [evaluate_cause(sim, cause) for cause in causes]
    failed = [row for row in rows if not row["holds"]]
    strength = min((row["closeness"] for row in rows), default=1.0)
    if hazard.get("causes_effect", "skip") == "skip":
        strength = 0.0 if failed else 1.0
    return {"checked": bool(causes), "conditions": rows, "failed": failed, "strength": strength}


def weakened(hazard: Dict[str, Any], strength: float) -> Dict[str, Any]:
    """A copy of the event at `strength` of its size; the original is untouched."""
    adjusted = dict(hazard)
    for field in SCALED_FIELDS:
        if field in adjusted:
            adjusted[field] = adjusted[field] * strength
    if "output_factor" in adjusted:
        adjusted["output_factor"] = 1.0 - (1.0 - adjusted["output_factor"]) * strength
    if isinstance(adjusted.get("values"), dict):
        adjusted["values"] = {key: (shift * strength if isinstance(shift, (int, float)) else shift)
                              for key, shift in adjusted["values"].items()}
    return adjusted


def effective_hazard(sim: Any, hazard: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """`(event as it stands now, report)`: the event itself when its causes hold or it has none, a weaker
    copy when it scales, None when it is skipped."""
    report = evaluate_causes(sim, hazard)
    if not report["failed"]:
        return hazard, report
    if report["strength"] <= 0.0:
        return None, report
    return weakened(hazard, report["strength"]), report


def failed_words(report: Dict[str, Any]) -> str:
    return "; ".join(row["why"] or row["quantity"] for row in report["failed"])


def cause_problems(hazard: Dict[str, Any], node_ids: Any) -> List[str]:
    """What is wrong with an event's causes, for `validate`."""
    name = hazard.get("name", "hazard")
    problems = []
    if hazard.get("causes_effect", "skip") not in EFFECTS:
        problems.append("%s: causes_effect must be one of %s" % (name, ", ".join(EFFECTS)))
    for cause in hazard.get("causes") or []:
        quantity = QUANTITIES.get(cause.get("quantity"))
        if quantity is None:
            problems.append("%s: unknown quantity %r (known: %s)"
                            % (name, cause.get("quantity"), ", ".join(sorted(QUANTITIES))))
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
