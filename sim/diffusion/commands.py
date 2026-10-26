"""Commands to diffusion, the owner of how knowledge spreads: literacy, the society's year, disclosure."""
from dataclasses import dataclass
from typing import Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class AdvanceSociety(Command):
	"""The society's own slow clock for `year`: schooling closes part of the literacy gap and taught trades become the
	society's own."""
	year: int


@dataclass(frozen=True)
class ApplyTechEffects(Command):
	"""A finished technique `node_id` changes what the society is like (values, literacy, the disease burden)."""
	node_id: str


@dataclass(frozen=True)
class Disclose(Command):
	"""The acting seat chooses what to do with an invention it made: `mode` is secret, license or publish. A licence
	names the `licensee` and the `fee` and `royalty` terms. Answers {"ok": True, "note"} or {"ok": False, "error"}."""
	node_id: str
	mode: str
	licensee: Optional[str] = None
	fee: float = 0.0
	royalty: float = 0.0


@dataclass(frozen=True)
class NoteFirstRuns(Command):
	"""The techniques some producer runs now (`in_use`): each is stamped with the year it was first seen running."""
	in_use: frozenset


@dataclass(frozen=True)
class RekeyDisclosures(Command):
	"""Seat `seat`'s licences and disclosures name `to_id` wherever they named `from_id`."""
	seat: str
	from_id: str
	to_id: str
