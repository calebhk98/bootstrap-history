"""Goals: the formal goal, the year each goal was reached, and what a measurement goal reads.

A goal need not be a thing you build. "Raise literacy past a fifth" or "cut most of what epidemics take" are states of
the whole society, not a project with hours and materials (data/branches/meta.goals says why a threshold is still modelled
as a node): it completes itself the moment a live measurement crosses its target."""
from typing import Any, Dict, List, Optional, Tuple

AnatomyRow = Tuple[str, Any, str]


def win_condition_met(win_condition: Dict[str, Any], value: float) -> bool:
    """True when `value` stands on the right side of the condition's target for its comparison ("<=" or ">=");
    any other comparison is never met."""
    comparison_op, target = win_condition["op"], win_condition["value"]
    if comparison_op == ">=":
        return value >= target
    if comparison_op == "<=":
        return value <= target
    return False


def check_attribute_path(path: Any) -> None:
    """Raise for an attribute path that could reach into private or nested state."""
    if not isinstance(path, str) or path.startswith("_") or "." in path:
        raise ValueError("invalid win_condition attribute path %r" % path)


def attribute_number(path: str, attribute: Any) -> float:
    """The number an attribute-sourced condition reads; `attribute` is what the game holds under `path`."""
    if not isinstance(attribute, (int, float)):
        raise ValueError("win_condition attribute %r is not numeric" % path)
    return float(attribute)


def generation_share(total_kw: float, source_kw: float) -> float:
    """One source's share of all generation; zero when nothing generates."""
    return source_kw / total_kw if total_kw else 0.0


def epidemic_relief(surviving_fraction: float) -> float:
    """What is cut of an epidemic's harm, given the fraction of it that survives the defences."""
    return 1.0 - surviving_fraction


def record_year(goal_years: Dict[str, int], goal_year: Optional[int], goal: Optional[str], node_id: str, year: int) -> Optional[int]:
    """Note `year` as the year `node_id` was reached (the first time only); returns the formal goal's year, which
    follows only when `node_id` is the goal and none is set yet."""
    if node_id != goal:
        return goal_year
    goal_years.setdefault(node_id, year)
    return year if goal_year is None else goal_year


def measurement_rows(source: Optional[str], key: Any, breakdown: Optional[Dict[str, Any]], relief_entries: List[Dict[str, Any]],
                     metric: Optional[str], current: float) -> List[AnatomyRow]:
    """What the number behind a win_condition is made of, as (label, value, unit) rows: the condition's parts when it
    has known ones, then the current value."""
    rows: List[AnatomyRow] = []
    if source == "generation_share":
        rows += [("this source", breakdown["sources_kw"].get(key, 0.0), "kW"), ("all generation", breakdown["total_kw"], "kW")]
    elif metric == "epidemic_relief":
        rows += [(entry["label"], 1.0 - entry["factor"], "fraction") for entry in relief_entries]
    rows.append(("current", current, "fraction"))
    return rows


def describe_win_condition(node: Dict[str, Any], labels: Dict[str, str]) -> str:
    """The player-facing sentence for a node's win_condition: its own description, else the label for its metric (with the target
    as a percentage), else a plain statement of the comparison, so a metric with no label degrades rather than fails."""
    win_condition = node.get("win_condition") or {}
    if win_condition.get("description"):
        return str(win_condition["description"])
    metric, comparison_op, target = win_condition.get("metric"), win_condition.get("op"), win_condition.get("value")
    template = labels.get(metric)
    if template:
        return template % ("%d%%" % round((target or 0.0) * 100))
    return "a measurement (%s %s %s) is met" % (metric, comparison_op, target)
