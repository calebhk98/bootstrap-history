"""Commands to the owner of a seat's concerns."""
from dataclasses import dataclass
from typing import Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class OpenVenture(Command):
	"""Open a completed concern's doors (at `units` of an institution's capacity when given), as `open` does.
	Answers (did it open, the reply: a sentence, a Refusal or a LogLine)."""
	node_id: str
	units: Optional[float] = None


@dataclass(frozen=True)
class NoteOperatingChanged(Command):
	"""Something opened or closed a plant of the acting seat's business outside this module, so the `operating_version` moves and
	every memo keyed on what is operating is stale."""


@dataclass(frozen=True)
class ClearMothball(Command):
	"""Forget a stale mothball entry for a work that is being built again."""
	node_id: str


@dataclass(frozen=True)
class SellConcern(Command):
	"""Sell a concern the acting seat runs to the actor the exchange picks, at the price it sets. Answers {"ok", ...}."""
	node_id: str


@dataclass(frozen=True)
class RollOut(Command):
	"""Open more of a work that declares coverage, or open it, to cover `share` of the people who can use it. Answers (ok, text)."""
	node_id: str
	share: float
