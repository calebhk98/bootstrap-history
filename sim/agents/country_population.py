"""One `Population` per foreign country, stepped each year by the model the home country uses.

The cohorts live on the country's profile (saved with it). The first step seeds them from the profile's
population with the model's own stable age structure and fixes the calories the country's land feeds; every
later step feeds the same Population that supply, so births, deaths and the food ceiling are outcomes.
"""
from typing import Any, List

from sim.world import demography

from .records import CountryProfile
from .tuning_country import FOREIGN_FOOD_HEADROOM

BANDS = ("children", "working_age", "elderly")


def people_counted(profile: CountryProfile) -> float:
	"""The people in the country: its cohorts once they exist, else the figure it was seeded with."""
	return sum(profile.cohorts.values()) if profile.cohorts else profile.population


def _seed_of(country: str) -> int:
	return sum((index + 1) * ord(character) for index, character in enumerate(country)) % (2 ** 32)


def _adult_equivalents(people: demography.Population) -> float:
	return (people.children * demography.CHILD_CALORIE_EQUIVALENT + people.working_age
			+ people.elderly * demography.ELDERLY_CALORIE_EQUIVALENT)


def _seed_cohorts(profile: CountryProfile) -> None:
	people = demography.Population.stationary(profile.population, seed=_seed_of(profile.country))
	profile.cohorts = {band: getattr(people, band) for band in BANDS}
	profile.food_kcal_per_day = (FOREIGN_FOOD_HEADROOM * _adult_equivalents(people)
								 * demography.SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY)


def step_country(profile: CountryProfile) -> demography.StepFlows:
	"""Advance one foreign country's Population by a year on its fixed food supply."""
	if not profile.cohorts:
		_seed_cohorts(profile)
	people = demography.Population(seed=_seed_of(profile.country), **profile.cohorts)
	flows = people.step(profile.food_kcal_per_day, jitter=False)
	profile.cohorts = {band: getattr(people, band) for band in BANDS}
	return flows


def step_foreign_populations(registry: Any) -> List[str]:
	"""Step every foreign country's Population; the countries stepped, in name order."""
	home = registry.state.home_country
	stepped = []
	for country in sorted(registry.state.countries):
		if country != home:
			step_country(registry.state.countries[country])
			stepped.append(country)
	return stepped
