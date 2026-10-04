"""What controls a measurement goal's number right now (Complaints/69, 404).

A registry maps a metric name, or a win_condition `source` kind, to a function
returning rows {label, value, unit, note}. A metric with no entry gets the
generic answer: target, current value if readable, and a plain statement that
no breakdown exists yet.
"""

import operator

import sim.engine.ui_port as ui_port

from .screen_education import education_report

_COMPARE = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt}
_READ_ERRORS = (AttributeError, KeyError, TypeError, ValueError)

METRIC_ROWS = {}     # metric name -> function(sim, condition) -> rows
SOURCE_ROWS = {}     # win_condition source kind -> function(sim, condition) -> rows
METRIC_READERS = {}  # metric name -> function(sim) -> number
SOURCE_READERS = {}  # source kind -> function(sim, condition) -> number


def _row(label, value, unit="", note=""):
    return {"label": label, "value": value, "unit": unit, "note": note}


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _read_attribute(sim, condition):
    path = condition.get("path")
    if not isinstance(path, str) or not path or path.startswith("_") or "." in path:
        return None
    value = getattr(sim, path, None)
    return float(value) if _is_number(value) else None


def _read_generation_share(sim, condition):
    breakdown = sim.generation_breakdown_kw()
    total = breakdown.get("total_kw") or 0.0
    return breakdown.get("sources_kw", {}).get(condition.get("key"), 0.0) / total if total else 0.0


SOURCE_READERS["attribute"] = _read_attribute
SOURCE_READERS["generation_share"] = _read_generation_share
METRIC_READERS["epidemic_relief"] = lambda sim: 1.0 - sim.hazard_relief("staff_loss")[0]


def current_value(sim, condition):
    """The live number a win_condition measures, or None when it cannot be read."""
    metric = condition.get("metric")
    try:
        if condition.get("source") in SOURCE_READERS:
            return SOURCE_READERS[condition["source"]](sim, condition)
        if metric in METRIC_READERS:
            return METRIC_READERS[metric](sim)
        value = sim.civ.get(metric)
        return float(value) if _is_number(value) else None
    except _READ_ERRORS:
        return None


# ---- literacy ------------------------------------------------------------

def _literacy_rows(kind):
    def rows(sim, condition):
        report = education_report(sim)
        literacy = report["literacy"]
        schools = report["schools"]
        running = [school for school in schools if school["flow_added"] > 0]
        change = report.get("recent_change") or {}
        found = [
            _row("current", literacy[kind], "fraction"),
            _row("ceiling", literacy[kind + "_ceiling"], "fraction",
                 "the most it can reach with what is built now"),
            _row("next year", literacy[kind + "_next_year"], "fraction"),
            _row("schools running", len(running), "schools",
                 "of %d schooling institutions in view" % len(schools)),
            _row("schooling flow", report["schooling_flow"], "flow"),
            _row("flow with printing", report["effective_schooling_flow"], "flow",
                 "printing and information diffusion modify the flow"),
            _row("printing adopted", report["printing_adopted"], "fraction"),
            _row("farm share of working hours", report["farm_share_of_hours"], "fraction",
                 "labour not yet freed from farming"),
            _row("limited by", report["literacy_limited_by"], "", "the binding constraint"),
        ]
        if "since_year" in change:
            found.append(_row("change since %s" % change["since_year"], change.get(kind),
                              "fraction", "what the census line shows"))
        else:
            found.append(_row("recent change", None, "", change.get("note", "")))
        return found
    return rows


METRIC_ROWS["literacy_general"] = _literacy_rows("general")
METRIC_ROWS["literacy_elite"] = _literacy_rows("elite")


# ---- hazard relief ---------------------------------------------------------

def _relief_rows(sim, condition):
    found = []
    for entry in sim.hazard_relief_entries("staff_loss"):
        node_id = entry.get("node")
        hidden = bool(sim.fog and node_id and not sim.is_visible(node_id))
        found.append(_row("an unseen measure" if hidden else entry["label"],
                          round(1.0 - entry["factor"], 4), "fraction",
                          "partly lapsed" if entry.get("lapsed_node") else ""))
    if not found:
        found.append(_row("measures in place", 0, "", "nothing you have built cuts this harm yet"))
    found.append(_row("total relief", round(current_value(sim, condition) or 0.0, 4), "fraction",
                      "each measure removes a share of what is left, so they compound"))
    return found


METRIC_ROWS["epidemic_relief"] = _relief_rows


# ---- sources ---------------------------------------------------------------

def _attribute_rows(sim, condition):
    value = _read_attribute(sim, condition)
    return [_row(condition.get("path"), value, "", "read directly from the game")] if value is not None else []


def _generation_rows(sim, condition):
    breakdown = sim.generation_breakdown_kw()
    return [_row("this source", breakdown.get("sources_kw", {}).get(condition.get("key"), 0.0), "kW"),
            _row("all generation", breakdown.get("total_kw") or 0.0, "kW"),
            _row("share", current_value(sim, condition), "fraction")]


SOURCE_ROWS["attribute"] = _attribute_rows
SOURCE_ROWS["generation_share"] = _generation_rows


# ---- assembly --------------------------------------------------------------

def _target(condition, current):
    operation, target = condition.get("op"), condition.get("value")
    if operation not in _COMPARE or not _is_number(target):
        return {"op": operation, "value": target, "gap": None, "met": None}
    if current is None:
        return {"op": operation, "value": target, "gap": None, "met": None}
    shortfall = target - current if operation in (">=", ">") else current - target
    return {"op": operation, "value": target, "gap": round(max(0.0, shortfall), 4),
            "met": bool(_COMPARE[operation](current, target))}


def anatomy_for(sim, condition, description=None):
    """The reply for one win_condition dict (or {"metric": name} with no target)."""
    builder = SOURCE_ROWS.get(condition.get("source")) or METRIC_ROWS.get(condition.get("metric"))
    current = current_value(sim, condition)
    rows = []
    if builder is not None:
        try:
            rows = builder(sim, condition)
        except _READ_ERRORS:
            builder = None
    reply = {"ok": True, "metric": condition.get("metric"), "description": description,
             "current": None if current is None else round(current, 4),
             "target": _target(condition, current), "rows": rows, "generic": builder is None}
    if builder is None:
        reply["note"] = ("no breakdown is available for this metric yet (Complaint 404); "
                         "the target and current value are all the game reports")
    return reply


def goal_condition(sim):
    """(win_condition, description) of the current goal, or (None, None) for a research goal."""
    node = sim.nodes.get(sim.goal) or {}
    condition = node.get("win_condition")
    return (condition, ui_port.win_condition_describe(node)) if condition else (None, None)


def conditions_for_metric(sim, metric):
    """(condition, description) for each visible goal naming this metric, unmet first, by target."""
    found = []
    for node_id in sorted(sim.nodes):
        condition = sim.nodes[node_id].get("win_condition")
        if not condition or condition.get("metric") != metric:
            continue
        if sim.fog and not sim.is_visible(node_id):
            continue
        found.append((node_id in sim.done, condition.get("value") or 0.0, node_id, condition))
    found.sort(key=lambda item: item[:3])
    return [(condition, ui_port.win_condition_describe(sim.nodes[node_id]))
            for _, _, node_id, condition in found]


def known_metrics(sim):
    """Metric names the player can ask about: those with a rule and those goals measure."""
    names = set(METRIC_ROWS)
    for node_id, node in sim.nodes.items():
        condition = node.get("win_condition")
        if condition and condition.get("metric") and not (sim.fog and not sim.is_visible(node_id)):
            names.add(condition["metric"])
    return sorted(names)
