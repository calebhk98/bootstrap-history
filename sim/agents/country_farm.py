"""A foreign country's farm: the home country's agriculture model (sim/world/agriculture*.py) over the country's own land.

The cleared area is what feeds the seeded people on the ground the country holds (its `arable_hectares` if declared,
else the hectares its home tiles can crop in a year, else no ceiling), and its quality is that ground's best-first
yield factor (soil, climate, river water). Each year
the farm workers the people need sow, reap and bank into the country's granary; what is eaten sets the Population's
nutrition. All of it lives in `profile.farm`, so it saves with the profile.
"""
import random
from typing import Any, Dict, Optional

from sim.geography.api import crop_site
from sim.world import agriculture, demography, farming_technique, land

STOCK_KG = "stock_kg"
WORKER_SEARCH_STEPS = 12


def farm_state(profile: Any) -> Dict[str, float]:
	"""The country's farm figures: hectares, quality, stock_kg, harvest_kg, shortfall_kg (empty before its first year)."""
	return profile.farm


def _arable_ground(profile: Any) -> Any:
	"""(arable hectares ceiling or None, best-first ladder of (fertility, hectares)) for the ground the country holds."""
	declared = profile.extra.get("arable_hectares")
	if declared is not None:
		quality = float(profile.extra.get("farm_quality", 1.0))
		return float(declared), [(quality, float(declared))]
	if profile.home_tiles:
		share = 1.0 - farming_technique.DEFAULT_TECHNIQUE.rotation.fallow_share_of_holding
		territory = land.territory_cropland({tile_id: crop_site(tile_id, share) for tile_id in profile.home_tiles})
		return territory.cropped_hectares, territory.ladder
	return None, []


def _open_farm(profile: Any, adult_equivalents: float) -> None:
	_ceiling, ladder = _arable_ground(profile)
	hectares = agriculture.farmland_for_population(adult_equivalents, ladder=ladder).hectares
	quality = land.ladder_quality(ladder, hectares) if ladder else 1.0
	profile.farm = {"hectares": hectares, "quality": quality, STOCK_KG: 0.0, "harvest_kg": 0.0, "shortfall_kg": 0.0,
					"years": 0.0}


def adult_equivalents(people: demography.Population) -> float:
	return (people.children * demography.CHILD_CALORIE_EQUIVALENT + people.working_age
			+ people.elderly * demography.ELDERLY_CALORIE_EQUIVALENT)


def _balance_kg(farm: Dict[str, float], technique: Any, workers: float, needy: float) -> float:
	"""Grain left after seed, spoilage and the people's year at average weather, working with `workers`."""
	hectares_worked = min(farm["hectares"], workers * agriculture.hectares_cropped_per_farm_worker(
		technique.crop, technique.toolkit))
	year = agriculture.Storage(stock_kg=farm[STOCK_KG]).step(
		agriculture.Land(hectares_worked, quality=farm["quality"]),
		hectares_worked * farming_technique.hours_per_hectare(technique), needy, crop=technique.crop,
		rotation=technique.rotation, toolkit=technique.toolkit, worker_count=workers, weather_multiplier=1.0)
	return year.gross_harvest_kg - year.seed_sown_kg - year.spoilage_kg - year.food_demand_kg


def farm_workers_to_feed(farm: Dict[str, float], technique: Any, needy: float, working_age: float) -> float:
	"""The fewest farm workers (full-time equivalents) that feed `needy` adult equivalents on the cleared land in an
	average year, found by bisection; every hand the land can crop (up to the working age) when none can."""
	ceiling = min(working_age, farm["hectares"] / agriculture.hectares_cropped_per_farm_worker(
		technique.crop, technique.toolkit))
	if _balance_kg(farm, technique, ceiling, needy) < 0.0:
		return ceiling
	low, high = 0.0, ceiling
	for _ in range(WORKER_SEARCH_STEPS):
		middle = (low + high) / 2.0
		low, high = (middle, high) if _balance_kg(farm, technique, middle, needy) < 0.0 else (low, middle)
	return high


def harvest_year(profile: Any, people: demography.Population, weather_stream: random.Random,
				 weather_multiplier: Optional[float] = None) -> float:
	"""Run the country's farming year for `people`; the calories a day each adult equivalent's share eats.
	The weather is one draw from `weather_stream`, or `weather_multiplier` when the caller fixes it."""
	needy = adult_equivalents(people)
	if not profile.farm:
		_open_farm(profile, needy)
	farm = profile.farm
	technique = farming_technique.DEFAULT_TECHNIQUE
	hectares_per_worker = agriculture.hectares_cropped_per_farm_worker(technique.crop, technique.toolkit)
	workers = farm_workers_to_feed(farm, technique, needy, people.working_age)
	hectares_worked = min(farm["hectares"], workers * hectares_per_worker)
	crop_workers = hectares_worked / hectares_per_worker
	if weather_multiplier is None:
		weather_multiplier = agriculture.draw_weather_multiplier(weather_stream)
	storage = agriculture.Storage(stock_kg=farm[STOCK_KG])
	reserve_target_kg = agriculture.granary_capacity_kg(
		needy * agriculture.annual_food_demand_kg_per_person(technique.crop))
	year = storage.step(
		agriculture.Land(hectares_worked, quality=farm["quality"]), hectares_worked * farming_technique.hours_per_hectare(technique),
		needy, crop=technique.crop, rotation=technique.rotation, toolkit=technique.toolkit,
		worker_count=crop_workers, reserve_target_kg=reserve_target_kg, weather_multiplier=weather_multiplier)
	capacity_kg = agriculture.granary_capacity_kg(year.food_demand_kg)
	farm[STOCK_KG] = max(0.0, min(agriculture.stock_to_carry_forward_kg(year), capacity_kg))
	farm["harvest_kg"] = year.gross_harvest_kg
	farm["shortfall_kg"] = year.food_shortfall_kg
	farm["years"] += 1.0
	return year.food_available_kcal_per_day
