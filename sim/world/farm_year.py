"""One year of the farm model for a society: the hectares its farm workers crop, the harvest, and the granary stock
carried into next year. Plain arithmetic over what the caller hands in; reads no simulation."""
import collections

from sim.world import agriculture, farming_technique

FarmYear = collections.namedtuple("FarmYear", "farm_year stock_kg")


def hectares_worked(farm_land, technique, farm_workers_fte):
    """Hectares the workers can crop with the technique, never more than the land holds."""
    per_worker = agriculture.hectares_cropped_per_farm_worker(technique.crop, technique.toolkit)
    return min(farm_land.hectares, farm_workers_fte * per_worker)


def run_farm_year(farm_land, technique, farm_stock_kg, adult_equivalent_population, farm_workers_fte, storage_seed,
                  weather_multiplier):
    """Sow, harvest, eat and store one year. Seed is charged on the hectares worked, not the whole endowment. The
    granary opens at `farm_stock_kg`; the reserve target lets a full granary feed people above subsistence; the stock
    carried forward is capped at the granary's capacity but a debt in seed corn passes through. Returns a `FarmYear`:
    the storage year and the stock left."""
    hectares_per_worker = agriculture.hectares_cropped_per_farm_worker(technique.crop, technique.toolkit)
    worked = hectares_worked(farm_land, technique, farm_workers_fte)
    crop_workers_fte = worked / hectares_per_worker
    farm_labour_hours = worked * farming_technique.hours_per_hectare(technique)
    worked_land = agriculture.Land(worked, quality=farm_land.quality)
    storage = agriculture.Storage(stock_kg=farm_stock_kg, seed=storage_seed)
    reserve_target_kg = agriculture.granary_capacity_kg(
        adult_equivalent_population * agriculture.annual_food_demand_kg_per_person(technique.crop))
    farm_year = storage.step(
        worked_land, farm_labour_hours, adult_equivalent_population,
        crop=technique.crop, rotation=technique.rotation, toolkit=technique.toolkit,
        worker_count=crop_workers_fte, reserve_target_kg=reserve_target_kg, weather_multiplier=weather_multiplier)
    capacity_kg = agriculture.granary_capacity_kg(farm_year.food_demand_kg)
    # a granary cannot hold less than nothing: seed sown beyond the stock is not a debt
    carried = max(0.0, min(agriculture.stock_to_carry_forward_kg(farm_year), capacity_kg))
    return FarmYear(farm_year, carried)
