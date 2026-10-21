"""The levers a state pulls on who holds land: confiscation and land reform, for any state.

`confiscation` is a share of every private holding on the state's tiles that passes to the state once (the engine clears the
lever when it has acted); `land_reform` is the most of a tile one private holder may keep, the excess that he lets out
passing to his tenants on it, every year while set. Both move titles (`land_moves.py`) and feed grievances (`unrest.py`).
"""
from typing import Any, Dict, Optional, Union

from sim.refusal import Refusal

CONFISCATION, LAND_REFORM = "confiscation", "land_reform"
LAND_KINDS = (CONFISCATION, LAND_REFORM)
LIMITS = {CONFISCATION: (0.0, 1.0, "a share of every private holding"),
		  LAND_REFORM: (0.0, 1.0, "the most of a tile one holder may keep")}


def set_land_lever(levers: Dict[str, Any], kind: str, value: Any, number, refuse) -> Union[Dict[str, Any], Refusal]:
	"""Set (None clears) a land lever of `levers`; `number` and `refuse` are the lever module's own checks."""
	before = levers.get(kind)
	if value is None:
		levers.pop(kind, None)
		return {"lever": kind, "name": None, "before": before, "after": None}
	low, high, what = LIMITS[kind]
	figure = number(value, low, high, what)
	if isinstance(figure, Refusal):
		return figure
	levers[kind] = figure
	return {"lever": kind, "name": None, "before": before, "after": figure}


def confiscation_share(record: Any) -> float:
	return float(record.levers.get(CONFISCATION, 0.0))


def reform_cap(record: Any) -> Optional[float]:
	"""The most of a tile a private holder may keep, or None when no reform is set."""
	value = record.levers.get(LAND_REFORM)
	return None if value is None else float(value)
