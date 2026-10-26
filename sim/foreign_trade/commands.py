"""Commands to the owner of the partner economies' books."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class SettleFlow(Command):
	"""The acting seat bought `tonnes` worth `value` of home money from a partner: the partner is paid in its own coin's
	metal and the flow is noted against the route's lift."""
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
