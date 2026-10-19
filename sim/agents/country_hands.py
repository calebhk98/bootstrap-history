"""What a foreign country has to give its state: working-age people, the farm hands its farm needs, and last year's food."""
from typing import Optional

from sim.world import agriculture, demography, farming_technique

from .country_farm import adult_equivalents, farm_workers_to_feed
from .headcount import Hands
from .records import CountryProfile


def hands_of(profile: CountryProfile) -> Optional[Hands]:
	"""None until the country's Population has stepped (its people are then only a seeded figure, with no ages)."""
	if not profile.cohorts:
		return None
	people = demography.Population(**profile.cohorts)
	working_age = float(profile.cohorts["working_age"])
	farm = profile.farm
	if not farm:
		return Hands(working_age, 0.0, 1.0)
	technique = farming_technique.DEFAULT_TECHNIQUE
	needy = adult_equivalents(people)
	farm_hands = farm_workers_to_feed(farm, technique, needy, working_age)
	need_kg = needy * agriculture.annual_food_demand_kg_per_person(technique.crop)
	food_ratio = 1.0 if need_kg <= 0.0 else 1.0 - min(1.0, farm.get("shortfall_kg", 0.0) / need_kg)
	return Hands(working_age, farm_hands, food_ratio)
