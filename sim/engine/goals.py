"""Goals: the formal goal, the year each goal was reached, and the anatomy of a measurement goal."""

from typing import Any, Callable, Dict, List, Tuple

AnatomyRow = Tuple[str, Any, str]


class GoalsMixin:
    # metric name -> function(sim, condition) -> [(label, value, unit)]; mods add their own metrics here.
    WIN_CONDITION_ANATOMY: Dict[str, Callable[[Any, dict], List[AnatomyRow]]] = {}

    def forget_goal_caches(self):
        """Drop everything derived from the current goal."""
        for name in ("_goal_closure", "_goal_critical_floor"):
            self.__dict__.pop(name, None)

    def record_goal_reached(self, node_id, year):
        """Note the year a node was reached; the formal goal's own year follows."""
        if node_id != self.goal:
            return
        self.state.scenario.goal_years.setdefault(node_id, year)
        if self.state.scenario.goal_year is None:
            self.state.scenario.goal_year = year

    def set_goal(self, node_id):
        """Make a node the formal goal. A goal reached before keeps the year it was reached in."""
        self.goal = node_id
        self.state.scenario.goal_year = self.state.scenario.goal_years.get(node_id)

    def win_condition_anatomy(self, condition) -> List[AnatomyRow]:
        """What the number behind a win_condition is made of right now, as (label, value, unit) rows."""
        metric = condition.get("metric")
        if metric in self.WIN_CONDITION_ANATOMY:
            return list(self.WIN_CONDITION_ANATOMY[metric](self, condition))
        rows = []
        if condition.get("source") == "generation_share":
            breakdown = self.generation_breakdown_kw()
            rows += [("this source", breakdown["sources_kw"].get(condition.get("key"), 0.0), "kW"),
                     ("all generation", breakdown["total_kw"], "kW")]
        elif metric == "epidemic_relief":
            rows += [(entry["label"], 1.0 - entry["factor"], "fraction")
                     for entry in self.hazard_relief_entries("staff_loss")]
        rows.append(("current", self._win_condition_value(condition), "fraction"))
        return rows
