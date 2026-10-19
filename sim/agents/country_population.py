"""One `Population` per foreign country, stepped each year by the model the home country uses.

The cohorts live on the country's profile (saved with it). The first step seeds them from the profile's
population with the model's own stable age structure and fixes the calories the country's land feeds; every
later step feeds the same Population that supply, so births, deaths and the food ceiling are outcomes.
"""
from typing import Any, List, Set

from sim.world import demography

from .country_disease import circulating_in, disease_deaths
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


def step_country(profile: CountryProfile, world: Any = None, circulating_elsewhere: Set[str] = frozenset()
				 ) -> demography.StepFlows:
	"""Advance one foreign country's Population by a year on its fixed food supply, with the year's epidemics
	(the home nation's disease model) when the world says which year and seed it is."""
	if not profile.cohorts:
		_seed_cohorts(profile)
	people = demography.Population(seed=_seed_of(profile.country), **profile.cohorts)
	epidemic_deaths = None
	if world is not None and (profile.disease_records or profile.disease_arrivals or circulating_elsewhere
							  or profile.extra.get("disease_exposure")):
		seed_text = "disease:%s:%d" % (profile.country, world.rng_for("disease", profile.country).getrandbits(32))
		epidemic_deaths = disease_deaths(
			profile, {band: float(profile.cohorts[band]) for band in BANDS},
			people.nutrition_ratio(profile.food_kcal_per_day), world.year, seed_text, circulating_elsewhere)
	flows = people.step(profile.food_kcal_per_day, jitter=False, epidemic_deaths=epidemic_deaths)
	profile.cohorts = {band: getattr(people, band) for band in BANDS}
	return flows


def step_foreign_populations(registry: Any, world: Any = None) -> List[str]:
	"""Step every foreign country's Population; the countries stepped, in name order. The pathogens in
	circulation at the start of the year are the contact every country draws against."""
	home = registry.state.home_country
	foreign = {name: registry.state.countries[name] for name in sorted(registry.state.countries) if name != home}
	circulating = circulating_in(foreign.values())
	for profile in foreign.values():
		step_country(profile, world, circulating)
	return list(foreign)
