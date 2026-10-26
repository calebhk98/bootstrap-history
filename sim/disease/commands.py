"""Commands to the owner of the epidemics."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class RunEpidemicYear(Command):
	"""The year's epidemics run against a people fed `food_kcal_per_day`, each playing seat's people and cash are cut by what
	they killed, and the year's burden and endemic death rates are read. Answers {deaths: {band: deaths}, burden,
	endemic_death_rates, deaths_by_tile: {tile: {band: deaths}}}."""
	food_kcal_per_day: float
	year: int
