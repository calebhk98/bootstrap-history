"""A state's wanted headcount checked against the people and the food its country has.

The people a state takes into its army, offices and works come from the working age. Some of that working age must
farm to feed the country; the rest are free to be taken, and fewer of them can be kept when the country's food
supply has fallen short. `fit` answers how many of the wanted head count the country can spare, and why not all.
"""
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

from .budget_line import Line

WORKING_AGE = "working_age"   # the state wants more people than the country has of working age
FARM_HANDS = "farm_hands"     # the rest of the working age is needed on the farms to feed the country
FOOD = "food"                 # last year's food fell short, so fewer can be kept from the fields


@dataclass(frozen=True)
class Hands:
	"""What a country has to give a state: its working-age people, the farm hands its food needs, and how much of
	the people's food need last year's supply (harvest and granary) met (1 is all of it)."""
	working_age: float
	farm_hands: float
	food_ratio: float


@dataclass(frozen=True)
class Headcount:
	wanted: float
	granted: float
	shortfall: float
	cause: Optional[str]

	def as_record(self) -> Dict[str, Any]:
		return {"wanted": self.wanted, "granted": self.granted, "shortfall": self.shortfall, "cause": self.cause}


def people_in(lines: Iterable[Line]) -> float:
	"""People the lines keep, of any trade."""
	return sum(sum(line.labour.values()) for line in lines)


def fit(wanted: float, hands: Optional[Hands], claimed_elsewhere: float = 0.0) -> Headcount:
	"""How many of `wanted` the country can spare after `claimed_elsewhere` (the state's other people). With no
	account of the country's hands the wish stands."""
	wanted = max(0.0, wanted)
	if hands is None:
		return Headcount(wanted, wanted, 0.0, None)
	people_limit = max(0.0, hands.working_age - claimed_elsewhere)
	farm_limit = max(0.0, people_limit - hands.farm_hands)
	granted = min(wanted, farm_limit * max(0.0, min(1.0, hands.food_ratio)))
	if granted >= wanted:
		return Headcount(wanted, wanted, 0.0, None)
	cause = WORKING_AGE if wanted > people_limit else FARM_HANDS if wanted > farm_limit else FOOD
	return Headcount(wanted, granted, wanted - granted, cause)


def checked_army(world: Any, record: Any, wanted: float, soldiers: float, claimed_elsewhere: float) -> Tuple[float, float]:
	"""(soldiers to pay this year, wanted force within what the country can spare); the check is booked on the
	record. An army larger than the country can spare disbands to it at once."""
	result = fit(wanted, world.state_hands(), claimed_elsewhere)
	record.headcount["army"] = result.as_record()
	return min(soldiers, result.granted), result.granted
