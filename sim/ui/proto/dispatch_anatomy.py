"""`anatomy`: what controls a measurement goal's number right now (Complaint 69)."""

import difflib

from .anatomy import anatomy_for, conditions_for_metric, goal_condition, known_metrics, METRIC_ROWS
from .command_registry import command


def _goal_form(sim):
    if sim.fog and sim.goal in sim.nodes and not sim.is_visible(sim.goal):
        return {"ok": False, "error": "your goal is not yet in view, so its anatomy is not shown. "
                "Name a metric instead, e.g. 'anatomy <metric>'; 'anatomy list' names them."}
    condition, description = goal_condition(sim)
    if condition is None:
        return {"ok": True, "research_goal": True,
                "note": "anatomy explains measurement goals (a number that must reach a level). "
                        "Your goal is a research goal: 'path' shows the way to it and "
                        "'leverage' shows what would move it fastest."}
    return anatomy_for(sim, condition, description)


def _named_form(sim, name):
    metric = name.strip().lower()
    names = known_metrics(sim)
    if metric not in names:
        close = difflib.get_close_matches(metric, names, n=3, cutoff=0.5)
        hint = ("did you mean: %s. " % ", ".join(close)) if close else ""
        return {"ok": False, "error": "no metric called %r. %s'anatomy list' names the metrics."
                % (name, hint)}
    matches = conditions_for_metric(sim, metric)
    condition, description = matches[0] if matches else ({"metric": metric}, None)
    return anatomy_for(sim, condition, description)


@command("anatomy", shape="word", group="overview", aliases=("controls", "anat"),
         summary="what controls a measurement goal's number right now",
         usage=["anatomy", "anatomy <metric>", "anatomy list"],
         options={"<metric>": "a measured quantity such as literacy_general; 'anatomy list' names them"},
         description="For the current goal when it is a measurement, or for a named metric: the "
                     "target, the current value and the gap, then the parts that set the number "
                     "today. A metric without a breakdown says so and shows target and value.")
def _cmd_anatomy(sim, nodes, cmd, ended):
    what = cmd.get("what") or cmd.get("metric")
    if what is None or str(what).lower() == "goal":
        return _goal_form(sim)
    if str(what).lower() == "list":
        metrics = known_metrics(sim)
        return {"ok": True, "metrics": metrics,
                "with_breakdown": [name for name in metrics if name in METRIC_ROWS]}
    return _named_form(sim, str(what))
