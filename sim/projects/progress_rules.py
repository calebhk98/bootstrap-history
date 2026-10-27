"""How a project in hand draws its founder hours and its hired trades each year, as functions of the figures they use."""
from typing import Any, Callable, Dict, List, Mapping, Optional


def hour_pace(ph_left: float, node_hours: float, node_years: float) -> float:
	"""How many of the founder's own hours a project would draw this year if nothing else competed for the pool: its
	hours left, or its nominal yearly pace, whichever is more."""
	return max(ph_left, node_hours / max(node_years, 1.0))


def max_span_years(floor_years: float, node_years: float, multiple: float) -> float:
	"""The most years a project may spend trying to find enough of a hired trade before it is given up on: a working
	lifetime, or `multiple` times the node's own calendar floor for a node the tree already marks as diffusion-limited."""
	return max(floor_years, float(node_years) * multiple)


def effective_lab_left(record: Mapping[str, Any], node: Mapping[str, Any]) -> Dict[str, float]:
	"""What is left of each hired trade's total for a project in hand, read-only. A record without the field (a
	hand-built simulation, a diagnostic caller) estimates the remaining trade work from the founder hours left."""
	lab_left = record.get("lab_left")
	if lab_left is not None:
		return lab_left
	left_frac = min(1.0, record.get("ph_left", node["ph"]) / max(1.0, node["ph"]))
	return {trade: want * left_frac for trade, want in node["lab"].items()}


def trade_draw_plan(node: Mapping[str, Any], lab_left: Optional[Mapping[str, float]], crew_rate_multiple: float
                    ) -> Dict[str, Dict[str, float]]:
	"""What a project would like to draw from each hired trade this year if the trade could supply it without limit.
	`lab_left` None means a project that has not started yet, so the full want is still owed."""
	out: Dict[str, Dict[str, float]] = {}
	for trade_id in sorted(node["lab"]):
		want = node["lab"][trade_id]
		left = want if lab_left is None else lab_left.get(trade_id, 0.0)
		if left <= 0 or want <= 0:
			continue
		nominal = want / max(1.0, node["yrs"])
		ceiling = nominal * crew_rate_multiple
		out[trade_id] = {"nominal": nominal, "left": left, "ceiling": ceiling, "desired": min(left, ceiling)}
	return out


def shortage_kind(supply: float, need: float, total_demand: Optional[float]) -> Optional[str]:
	"""Why a trade is short for a project that wants `need` hours a year of it: "staffing" when the society cannot field
	that much at all, "booked" when it can but the portfolio's demand exceeds it, else None. `total_demand` None means
	the caller already knows the project fell short, so what the society can field decides between the two."""
	if supply < need:
		return "staffing"
	if total_demand is None or total_demand > supply + 1e-6:
		return "booked"
	return None


def shortfall_note(record: Mapping[str, Any]) -> str:
	"""The step-log reason for a project short of hired trades: booked by other work, or more than the society can field
	at all."""
	short = sorted(record.get("short_of_trade") or [])
	staffing = [trade_id for trade_id in short if trade_id in (record.get("short_of_trade_staffing") or [])]
	booked = [trade_id for trade_id in short if trade_id not in staffing]
	if booked:
		return "trade hours already booked: " + ", ".join(booked[:2])
	return "nobody to do the work: this society cannot field enough " + ", ".join(staffing[:2])


def short_trades(lab_left: Mapping[str, float], node: Mapping[str, Any], available_of: Callable[[str], float]) -> List[str]:
	"""Up to three trades still owed hours whose free hours (`available_of(trade)`) fall short of this year's pace."""
	return sorted(
		trade_id for trade_id, left in lab_left.items()
		if left > 0 and available_of(trade_id) < min(left, node["lab"][trade_id] / max(1.0, node["yrs"])))[:3]
