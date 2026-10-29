"""Goals: the formal goal, the year each goal was reached, a measurement goal's value and anatomy (the rules are goal_rules.py)."""
from typing import Any, Dict, List, Optional

from sim.knowledge.api import LearnTechnique
from sim.reporting.api import RecordEvent

from . import goal_rules
from .commands import ForgetGoalClosure, RecordGoalReached, RememberGoalClosure, RememberGoalFloor, SetGoal
from .goal_rules import AnatomyRow


class Goals:

    def goal(self) -> Dict[str, Any]:
        """The acting seat's formal goal: {node: its id or None, year: the year it was reached or None, years: the year each
        goal id was reached as the formal goal (the live record)}."""
        return {"node": self.seat.goal, "year": self.seat.goal_year, "years": self.seat.goal_years}

    def on_road_to_goal(self, node_id: str) -> bool:
        """Whether the goal needs this node. A yes or no with no distance, so it names no route the player has not already been
        shown. What the goal needs is worked out once and kept (the engine's other readers of it share the same set)."""
        needed = self.goal_closure()
        if needed is None:
            try:
                needed = self.needs.tree_closure(self.goal()["node"])
            except Exception:
                needed = set()
            self.remember_goal_closure(RememberGoalClosure(needed))
        return node_id in needed

    def goal_closure(self) -> Optional[Any]:
        """What the acting seat's goal needs, once worked out; None until then, and again after the goal changes."""
        return self._closures.get(self.clock.acting_seat)

    def goal_critical_floor(self) -> Optional[float]:
        """The shortest road in years to the acting seat's goal, once worked out; None until then, and again after the goal changes."""
        return self._critical_floors.get(self.clock.acting_seat)

    def remember_goal_floor(self, command: RememberGoalFloor) -> None:
        self._critical_floors[self.clock.acting_seat] = command.years

    def remember_goal_closure(self, command: RememberGoalClosure) -> None:
        self._closures[self.clock.acting_seat] = command.nodes

    def forget_goal_closure(self, command: ForgetGoalClosure) -> None:
        self._closures.pop(self.clock.acting_seat, None)
        self._critical_floors.pop(self.clock.acting_seat, None)

    def win_condition_text(self, node: Dict[str, Any]) -> str:
        """The sentence that says what a node's win_condition asks for."""
        return goal_rules.describe_win_condition(node, self.needs.win_condition_labels())

    def set_goal(self, command: SetGoal) -> None:
        """Make a node the formal goal. A goal reached before keeps the year it was reached in."""
        self.seat.goal = command.node_id
        self.forget_goal_closure(ForgetGoalClosure())
        self.seat.goal_year = self.seat.goal_years.get(command.node_id)

    def record_goal_reached(self, command: RecordGoalReached) -> None:
        """Note the year a node was reached; the formal goal's own year follows."""
        self.seat.goal_year = goal_rules.record_year(self.seat.goal_years, self.seat.goal_year, self.seat.goal, command.node_id, command.year)

    def win_condition_value(self, condition: Dict[str, Any]) -> float:
        """The live number a win_condition's `metric` names, 0..1. Raises for a metric this engine does not know how to
        read - at load time, via `validate`, not mid-game - rather than silently reading 0 forever for a typo."""
        metric = condition.get("metric")
        if condition.get("source") == "staff":
            return goal_rules.staff_number(condition.get("key"), self.needs.staff())
        if condition.get("source") == "generation_share":
            breakdown = self.needs.generation_breakdown()
            return goal_rules.generation_share(breakdown["total_kw"], breakdown["sources_kw"].get(condition.get("key"), 0.0))
        if metric in ("literacy_general", "literacy_elite"):
            return self.needs.literacy(metric)
        if metric == "epidemic_relief":
            # the surviving fraction of the harm (1.0 = no protection at all); relief is what is cut
            return goal_rules.epidemic_relief(self.needs.hazard_relief("staff_loss")[0])
        raise ValueError("unknown win_condition metric %r" % metric)

    def win_condition_anatomy(self, condition: Dict[str, Any]) -> List[AnatomyRow]:
        """What the number behind a win_condition is made of right now, as (label, value, unit) rows."""
        provided = self.needs.win_condition_rows(condition)
        if provided is not None:
            return list(provided)
        metric = condition.get("metric")
        breakdown = self.needs.generation_breakdown() if condition.get("source") == "generation_share" else None
        entries = self.needs.hazard_relief_entries("staff_loss") if breakdown is None and metric == "epidemic_relief" else []
        return goal_rules.measurement_rows(condition.get("source"), condition.get("key"), breakdown, entries, metric,
                                           self.win_condition_value(condition))

    def check_win_conditions(self, seat_id: Optional[str] = None) -> None:
        """Once a year: every node carrying a `win_condition` that is not already done is checked against the live
        measurement it names, and completes itself like a normal completion (held, dated, logged, goal year if it is the
        goal) but with no cost charged and no effects applied, because nobody did any work; a measurement crossed a line.
        Walks the nodes that carry a win_condition in id order, which the tree fixes."""
        year = self.needs.year()
        held = self.needs.techniques_held()
        for node_id in self._win_condition_keys():
            if node_id in held:
                continue
            node = self.needs.tree[node_id]
            win_condition = node["win_condition"]
            if not win_condition:
                continue
            value = self.win_condition_value(win_condition)
            if not goal_rules.win_condition_met(win_condition, value):
                continue
            self.needs.send(LearnTechnique(node_id, year=year))
            self.needs.send(RecordEvent.in_year(year, "goal_achieved", "achieved: " + node["name"]))
            self.record_goal_reached(RecordGoalReached(node_id, year))

    def _win_condition_keys(self) -> List[str]:
        if self._conditioned is None:
            self._conditioned = sorted(node_id for node_id, node in self.needs.tree_nodes().items() if node.get("win_condition"))
        return self._conditioned
