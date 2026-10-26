"""Commands to the owner of a seat's standing with its society and state (polity), and to the state's records (campaigns send
them)."""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class RaiseScandal(Command):
	"""The acting seat's scandal rises by `scandal`, this year's and last year's figure alike."""
	scandal: float


@dataclass(frozen=True)
class RecordBribe(Command):
	"""The acting household's scandal and the year's bribes are set to these figures, and its protection is worked
	out again from them."""
	scandal: float
	bribes_year_to_date: float


@dataclass(frozen=True)
class StrikeFromForce(Command):
	"""`killed` soldiers who died in the field come off the army line of the country `owner`'s state (nothing for an
	owner with no state)."""
	owner: str
	killed: float


@dataclass(frozen=True)
class SetLandTakenMemory(Command):
	"""The state of `owner` remembers the land taken from each tile's people as `by_tile` ({tile: memory})."""
	owner: str
	by_tile: Dict[str, float]


@dataclass(frozen=True)
class RegisterPeople(Command):
	"""The state of `owner` registers its people by tile: each count replaces the one held when it is larger."""
	owner: str
	by_tile: Dict[str, float]


@dataclass(frozen=True)
class SetGrievanceReference(Command):
	"""The level of grievance the state of `owner`'s taxpayers have grown used to."""
	owner: str
	reference: float


@dataclass(frozen=True)
class ResetStateUnrest(Command):
	"""The year's reading of the state of `owner` starts again: no tile has an unrest or a hold figure yet."""
	owner: str


@dataclass(frozen=True)
class SetTileReading(Command):
	"""The year's reading of one tile of the state of `owner`: the unrest of its people and how firmly the state
	holds it (the share of risings its garrison would put down)."""
	owner: str
	tile: str
	unrest: float
	hold: float


@dataclass(frozen=True)
class RecordRising(Command):
	"""A rising on the state of `owner` joins the record of its risings, of which the latest `kept` are kept."""
	owner: str
	entry: Dict[str, Any]
	kept: int


@dataclass(frozen=True)
class ReplaceRuler(Command):
	"""A won rising puts a new ruler of `age` on the throne of `owner`, backed by `backer`, and calls an accession."""
	owner: str
	age: int
	backer: str


@dataclass(frozen=True)
class CloseSuccessionDispute(Command):
	"""The challenger to the succession in the state of `owner` is dropped."""
	owner: str


@dataclass(frozen=True)
class SetValueWeights(Command):
	"""The society's value weights become `weights` ((name, weight) pairs): the civilisation's own, at the opening."""
	weights: tuple


@dataclass(frozen=True)
class ShiftValueWeight(Command):
	"""The society's value weight `field` moves by `delta`, held between the weight floor and ceiling. Answers
	(before, after), or a `Refusal` (cause `not_a_value_weight`) when the society has no such weight."""
	field: str
	delta: float


@dataclass(frozen=True)
class GainReputation(Command):
	"""The acting seat's reputation rises by `amount`, never above the top of the reputation scale."""
	amount: float


@dataclass(frozen=True)
class ScaleProtection(Command):
	"""The acting household's protection is multiplied by `share` (a patron dies and takes part of his cover with him)."""
	share: float


@dataclass(frozen=True)
class AddScandal(Command):
	"""The acting seat's scandal rises by `amount` (this year's figure only: the year's opening mark stays)."""
	amount: float


@dataclass(frozen=True)
class AddReputation(Command):
	"""The acting seat's reputation rises by `amount`, with no ceiling."""
	amount: float


@dataclass(frozen=True)
class SetReputation(Command):
	"""The acting seat's reputation is set to `value` (a trial figure the caller sets and puts back)."""
	value: float


@dataclass(frozen=True)
class ScaleFamiliarity(Command):
	"""The acting seat's familiarity is multiplied by `share` (people who knew the household no longer see it every day)."""
	share: float


@dataclass(frozen=True)
class AddGovernance(Command):
	"""The acting seat's governance standing rises by `amount`: a work finished that the state's own interests value."""
	amount: float


@dataclass(frozen=True)
class AnswerStateDemands(Command):
	"""The acting household answers the state's demands by `stance` from now on, offering `service` (money's worth) when it
	negotiates. Answers what the stance risks, in words."""
	stance: str
	service: float = 0.0


@dataclass(frozen=True)
class WithdrawFromPublicLife(Command):
	"""The acting household becomes a smaller man: reputation and eminence fall. Answers (done, text)."""


@dataclass(frozen=True)
class SettleWithState(Command):
	"""The acting household pays the state `amount`, or all of what `target` (`debt` or `claims`) names. Answers (paid, text)."""
	target: str
	amount: Optional[float] = None


@dataclass(frozen=True)
class CarryOutTransfers(Command):
	"""A finished work `node_id` that declares a `transfer` pays what it asks of the household once, and says so."""
	node_id: str


@dataclass(frozen=True)
class RenewStanding(Command):
	"""The first part of the acting seat's year of standing: reputation decays toward the floor and familiarity is renewed."""


@dataclass(frozen=True)
class CloseStandingYear(Command):
	"""The rest of the acting seat's year of standing: protection, the state's pressure, scandal, bribery and the hazards of
	denunciation and prominence."""
