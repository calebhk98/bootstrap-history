"""Commands to the owner of the partner economies' books."""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class SettleFlow(Command):
	"""The acting seat bought `tonnes` worth `value` of home money from a partner: the partner is paid in its own coin's
	metal and the flow is noted against the route's lift. Negative `tonnes` is a sale to the partner."""
	partner: str
	tonnes: float
	value: float


@dataclass(frozen=True)
class RecordStockTaken(Command):
	"""Smugglers took `units` of a material out of a partner's holding, so it has that much less to sell."""
	partner: str
	material: str
	units: float


@dataclass(frozen=True)
class CloseMarketsTo(Command):
	"""A partner's state shuts its markets to a party until a year."""
	partner: str
	party: str
	until: int


@dataclass(frozen=True)
class NoteActorTrade(Command):
	"""An actor carried `tonnes` of a material to a partner (`to_partner`) or from it this year; `landed_cost` is what a cargo
	to the partner cost its carrier to land (home money). A negative amount takes a part of a cargo back."""
	partner: str
	material: str
	tonnes: float
	to_partner: bool
	landed_cost: float = 0.0


@dataclass(frozen=True)
class NoteActorHomeTrade(Command):
	"""Actors landed `tonnes` of a material in the home market (`landing`) or took them out of it this year."""
	material: str
	tonnes: float
	landing: bool


@dataclass(frozen=True)
class NoteCargoLeg(Command):
	"""A trader shipped `tonnes` of a material from `source` to `destination` (places: `home` or a partner), booked at what it
	paid and was to receive; the same trader, route and good in one year is one leg, settled once the year's market has cleared.
	`duty` is the part of `carriage` that is the destination state's tariff."""
	trader_id: str
	material: str
	tonnes: float
	source: str
	destination: str
	paid: float
	received: float
	carriage: float
	home: str
	duty: float = 0.0


@dataclass(frozen=True)
class SettleTraderCargo(Command):
	"""Settle every noted cargo leg. `results` is what the agent economy's book gave each leg that entered it
	({leg id: {"tonnes", "money"}}); None when there was no book."""
	results: Optional[Dict[str, Dict[str, Any]]] = None


@dataclass(frozen=True)
class ClosePartnerBooks(Command):
	"""The year ends in the partners' markets: each partner's book clears on the year's actor cargo, and the tallies reset."""
