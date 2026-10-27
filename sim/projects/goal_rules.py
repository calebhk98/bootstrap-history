"""How finishing a project moves the goal: what a goal measure is called, how it is shown and how much it moved."""
from typing import Any, Dict, List, Mapping, Optional, Tuple

# What a goal measure is called and how it is shown; unknown metrics print raw.
FRACTION_METRICS = frozenset(("literacy_general", "literacy_elite", "epidemic_relief"))
# metric -> ((label, the literacy ceiling that bounds it),)
GOAL_DETERMINANTS = {
	"literacy_general": (("literacy ceiling", "literacy_general"),),
	"literacy_elite": (("elite literacy ceiling", "literacy_elite"),),
}
# a node's `risks` kinds taken from the held stock (crew is taken from the employees)
STOCK_RISKS = ("hull", "cargo")


def format_goal_value(value: float, is_fraction: bool) -> str:
	return "%.1f%%" % (value * 100.0) if is_fraction else "%.3g" % value


def goal_movement(before: Optional[Mapping[str, Any]], after: Optional[Mapping[str, Any]]) -> Tuple[List[Tuple[str, str, str]], int]:
	"""(label, before text, after text) for each goal measure that moved between two goal snapshots, plus the road steps
	gained."""
	if not before or not after:
		return [], 0
	moved = []
	for label, (old_value, is_fraction) in before["measures"].items():
		new_value = after["measures"].get(label, (old_value, is_fraction))[0]
		if abs(new_value - old_value) > 1e-9:
			moved.append((label, format_goal_value(old_value, is_fraction), format_goal_value(new_value, is_fraction)))
	return moved, after["road_done"] - before["road_done"]


def snapshot(measures: Dict[str, Tuple[float, bool]], road_done: int, road_total: int) -> Dict[str, Any]:
	"""The goal's live measure(s) and road progress."""
	return {"measures": measures, "road_done": road_done, "road_total": road_total}
