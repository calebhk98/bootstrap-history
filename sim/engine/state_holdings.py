"""What one seat holds and has told its player, apart from the world everyone shares."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HoldingsState:
	"""A seat's material stock."""
	market_pressure: float = 0.0
	_dashboard_history: Optional[List[Any]] = None


@dataclass
class SeatProgressState:
	"""A seat's dashboard cap, score reading and the one-time notes shown to its player."""
	dashboard_history_years: Optional[int] = None  # cap dashboard history to N most recent years; None = no cap
	_said_parallelism: Optional[bool] = None
	_said_command_index: Optional[bool] = None
	_said_explanations: Optional[Dict[str, int]] = None
	score_last_seen: Optional[Dict[str, Any]] = None
