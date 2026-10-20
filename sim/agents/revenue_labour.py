"""Labour owed to the state: days a year from each working-age person or each household, taken as hours.

A form on the basis `labour_days` declares `rate` (days a year), `per` (`working_age_person` or `household`), `to`
(`works`: the state's roads, buildings and walls; `army`: conscripts) and `commute` (the share paid in coin instead,
by the state's choice, at the going wage). The hours come off the working time of the people it falls on; what the
state gets is unpaid labour, which takes the place of the wages its works and army would cost.
"""
import dataclasses
from dataclasses import dataclass
from typing import Any, List, Tuple

from sim.constants import declare
from sim.world.climate_needs import PERSONS_PER_HOUSEHOLD

from .budget_line import Line
from .state_works import WORKS

BASIS = "labour_days"
WORKS_DUE = "works"
ARMY_DUE = "army"
DESTINATIONS = (WORKS_DUE, ARMY_DUE)
PERSON = "working_age_person"
HOUSEHOLD = "household"

HOURS_PER_WORKING_DAY = declare(
	"HOURS_PER_WORKING_DAY", 10.0, kind="engineering_estimate", unit="hours/day",
	source="The ten-hour day that HOURS_PER_PERSON_YEAR counts a working year in.", confidence="B",
	why="Turns the days of labour a state's levy names into hours of the working time of the people it falls on.")

# The lines of the budget that are works, which unpaid labour can take the place of.
WORK_LINES = frozenset({"roads", "public_buildings"} | {work.name for work in WORKS})


@dataclass(frozen=True)
class Levy:
	"""Labour owed under one form this year."""
	person_days: float
	people: float       # the people (or households) it falls on
	destination: str
	commute: float      # share paid in coin instead


def levy_of(declared: Any, world: Any) -> Levy:
	per = declared.get("per", PERSON)
	destination = declared.get("to", WORKS_DUE)
	commute = float(declared.get("commute", 0.0))
	if per not in (PERSON, HOUSEHOLD) or destination not in DESTINATIONS or not 0.0 <= commute <= 1.0:
		raise ValueError("form %r: labour is owed per %r|%r to %r|%r and commuted by a share of 0..1"
						 % (declared["form"], PERSON, HOUSEHOLD, WORKS_DUE, ARMY_DUE))
	people = world.national_people("labourer") if per == PERSON else world.population_total() / PERSONS_PER_HOUSEHOLD
	return Levy(float(declared["rate"]) * max(0.0, people), max(0.0, people), destination, commute)


def person_years(hours: float, world: Any) -> float:
	return hours / world.hours_per_person_year


def offset_upkeep(lines: List[Line], years: float) -> Tuple[List[Line], float]:
	"""The lines with the work lines' labour taken by `years` of unpaid labour, person-year for person-year (a work's
	person-years are plain labour: skill is not told apart), each line paying only for the labour that is left;
	and the years not used."""
	result = []
	for line in lines:
		people = sum(line.labour.values())
		if line.name in WORK_LINES and people > 0.0 and years > 0.0:
			taken = min(years, people)
			years -= taken
			left = 1.0 - taken / people
			line = dataclasses.replace(line, labour={trade: count * left for trade, count in line.labour.items()},
									   wages=line.wages * left)
		result.append(line)
	return result, years
