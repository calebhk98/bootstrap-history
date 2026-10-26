"""Campaigns' commands: what any actor that owns tiles sends to raise, order, recall or stand down an army."""
from dataclasses import dataclass
from typing import Any, Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class RaiseArmy(Command):
	"""Raise an army of `soldiers` of the owner's force on one of its tiles (its best-endowed one when `tile` is None).
	Answers the new `Army`, or a refusal with cause `army_size_not_positive`, `unknown_tile`, `tile_not_yours` or
	`not_enough_soldiers`."""
	owner: str
	soldiers: Any
	tile: Optional[str] = None


@dataclass(frozen=True)
class OrderArmy(Command):
	"""Send an army to a tile; it marches from the next campaign phase. Answers the army, or a refusal with cause
	`unknown_army`, `not_your_army` or `unknown_tile`."""
	owner: str
	army_id: Any
	tile: Any


@dataclass(frozen=True)
class RecallArmy(Command):
	"""Order an army back to the tile it was raised on, or to the owner's best-endowed tile if that is no longer the
	owner's. Answers the army, or a refusal (`unknown_army`, `not_your_army`, `no_tile_to_return_to`)."""
	owner: str
	army_id: Any


@dataclass(frozen=True)
class DisbandArmy(Command):
	"""Stand an army down: its soldiers go back to the state's force. Answers the army that was, or a refusal
	(`unknown_army`, `not_your_army`)."""
	owner: str
	army_id: Any
