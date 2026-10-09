"""What one seat holds and has told its player, apart from the world everyone shares."""
import collections
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HoldingsState:
	"""A seat's extractive workings, land, granary, material stock and shortage readings."""
	mines: List[Dict[str, Any]] = field(default_factory=list)
	mine_pending: Dict[str, float] = field(default_factory=dict)
	mine_ready: Dict[str, int] = field(default_factory=dict)
	mine_cost_paid: float = 0.0
	mine_tranches: Optional[List[Any]] = None
	shortages: collections.Counter = field(default_factory=collections.Counter)
	throttle: float = 1.0
	binding: Optional[str] = None
	shortage_condition: Optional[Dict[str, Any]] = None
	forest_ha: float = 0.0
	nitre_bed_m2: float = 0.0
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
	# tonnes a year per material the last throttle saw; the next year's prices read it before it is recomputed
	material_demand_at_last_throttle: Optional[Dict[str, float]] = None
	_dashboard_history: Optional[List[Any]] = None
	# rights and equity the seat holds as an actor: patents by node id, shares held by issuer id, and the part
	# of the seat's own equity issued to others
	patents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
	shares_held: Dict[str, float] = field(default_factory=dict)
	shares_issued: float = 0.0


@dataclass
class SeatProgressState:
	"""A seat's formal goal record, score reading and the one-time notes shown to its player."""
	goal_year: Optional[int] = None
	goal_years: Dict[str, int] = field(default_factory=dict)  # goal id -> year it was reached as the formal goal
	dashboard_history_years: Optional[int] = None  # cap dashboard history to N most recent years; None = no cap
	_said_scandal: int = 0
	_said_parallelism: Optional[bool] = None
	_said_command_index: Optional[bool] = None
	_said_explanations: Optional[Dict[str, int]] = None
	score_last_seen: Optional[Dict[str, Any]] = None
