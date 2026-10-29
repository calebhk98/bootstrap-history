"""Commands to the owner of a seat's concerns."""
from dataclasses import dataclass
from typing import Optional, Tuple

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


@dataclass(frozen=True)
class ShutForgotten(Command):
	"""The acting seat's works for `node_ids`, techniques it has just lost, are no longer running or shut for a time."""
	node_ids: Tuple[str, ...]


@dataclass(frozen=True)
class StopOperating(Command):
	"""The acting seat stops running the concerns `node_ids` (a plant that is shut for a time is left as it is)."""
	node_ids: Tuple[str, ...]


@dataclass(frozen=True)
class MothballConcern(Command):
	"""Switch off the plant of `node_id`, keeping its size and age, from `year` for `reason` (a closure reason)."""
	node_id: str
	year: int
	reason: str


@dataclass(frozen=True)
class RestoreConcern(Command):
	"""Switch a shut plant of `node_id` back on."""
	node_id: str


@dataclass(frozen=True)
class CloseConcern(Command):
	"""Stop running `node_id` altogether: its plant, with its size and staffing, is forgotten."""
	node_id: str


@dataclass(frozen=True)
class ForgetClosureReason(Command):
	"""Drop the record of why the plant of `node_id` is shut (only `reason`'s, when one is named). Answers whether one was dropped."""
	node_id: str
	reason: Optional[str] = None


@dataclass(frozen=True)
class ReviewConcerns(Command):
	"""The yearly review of the acting seat's business under the named `rules` (sim/agents/business_review.py). Answers the closures:
	what closed and why."""
	rules: Tuple[str, ...]


@dataclass(frozen=True)
class ReviewReopening(Command):
	"""Reopen the plants shut for want of staff that the acting seat can staff again. Answers the entry ids that reopened."""


@dataclass(frozen=True)
class NoteConcernYear(Command):
	"""Tally the year of the plant of `node_id`: its margin, and how many years running it has lost money."""
	node_id: str
	margin: float


@dataclass(frozen=True)
class WatchBusiness(Command):
	"""Seat `seat_id`'s business reports the opening and closing of its plants from here on (a new seat, a load or a seat switch
	needs it again)."""
	seat_id: str
