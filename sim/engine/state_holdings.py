"""What one seat holds and has told its player, apart from the world everyone shares."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class HoldingsState:
	"""A seat's material stock."""
	_dashboard_history: Optional[List[Any]] = None

	@property
	def dashboard_history(self) -> Optional[List[Any]]:
		return self._dashboard_history   # None until recorded

	@dashboard_history.setter
	def dashboard_history(self, history: Optional[List[Any]]) -> None:
		self._dashboard_history = history


@dataclass
class SeatProgressState:
	"""A seat's dashboard cap, score reading and the one-time notes shown to its player."""
	dashboard_history_years: Optional[int] = None  # cap dashboard history to N most recent years; None = no cap
	_said_parallelism: Optional[bool] = None
	_said_command_index: Optional[bool] = None
	_said_explanations: Optional[Dict[str, int]] = None
	score_last_seen: Optional[Dict[str, Any]] = None

	@property
	def said_parallelism(self) -> Optional[bool]:
		return self._said_parallelism

	@said_parallelism.setter
	def said_parallelism(self, said: Optional[bool]) -> None:
		self._said_parallelism = said

	@property
	def said_command_index(self) -> Optional[bool]:
		return self._said_command_index

	@said_command_index.setter
	def said_command_index(self, said: Optional[bool]) -> None:
		self._said_command_index = said

	@property
	def said_explanations(self) -> Optional[Dict[str, int]]:
		return self._said_explanations

	@said_explanations.setter
	def said_explanations(self, said: Optional[Dict[str, int]]) -> None:
		self._said_explanations = said
