"""What one seat holds and has told its player, apart from the world everyone shares."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HoldingsState:
	"""A seat's granary, farm and material stock."""
	market_pressure: float = 0.0
	_material_stock_ledger: Optional[Dict[str, float]] = None
	_material_stock_opening: Optional[Dict[str, Any]] = None
	farm_hectares: Optional[float] = None
	farm_stock_kg: float = 0.0
	farm_cleared_hectares: Optional[float] = None
	farm_last_shortfall_kg: Optional[float] = None
	# gross harvest of the last year the farm closed, in kilograms of grain (0 before the first)
	farm_last_harvest_kg: float = 0.0
	farm_last_marginal_product: Optional[float] = None
	farm_hours_needed: Optional[float] = None
	_dashboard_history: Optional[List[Any]] = None
	# settlements the seat has founded on tiles beyond its country's own: tile, year founded, and the three age
	# cohorts of the people there (sim/engine/colonies.py)
	colonies: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SeatProgressState:
	"""A seat's dashboard cap, score reading and the one-time notes shown to its player."""
	dashboard_history_years: Optional[int] = None  # cap dashboard history to N most recent years; None = no cap
	_said_parallelism: Optional[bool] = None
	_said_command_index: Optional[bool] = None
	_said_explanations: Optional[Dict[str, int]] = None
	score_last_seen: Optional[Dict[str, Any]] = None
