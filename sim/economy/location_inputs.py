"""Where a processor sits relative to the inputs it carries: material orientation.

A run that makes less mass than it consumes (smelting, milling) is cheaper to haul as product than as
input, so it settles where its inputs are made; one that makes more settles where its output is wanted.
The siting cost of a tile is the carriage of a run's fixed-site inputs in from where they are made plus the
carriage of its output out to where it is wanted, each by the recipe's own masses. Only fixed-site inputs pull:
what a mobile maker supplies is made beside its users, so it has no place to pull towards.

An input that only fixed sites can supply (the goods of a site-bound recipe with declared limits) also
bounds where its processors can be placed: only in market areas of that good that hold supply, ranked by
the supply an area offers that placed users have not claimed. What the supply there cannot
feed is built all the same, in proportion: the shortage is then the input's price (and the processor's idle
capacity), not a smaller opening.
"""
import math
from typing import Dict, Mapping, Sequence, Tuple

from . import sites
from .types import GoodId, GoodSpec, MarketArea, Recipe, TileId
from sim.unit_conversions import KILOGRAMS_PER_TONNE


def tonnes_of(goods: Mapping[GoodId, float], specs: Mapping[GoodId, GoodSpec]) -> Dict[GoodId, float]:
    """Mass in tonnes of each good's quantity; a good with nothing to carry is left out."""
    return {good: quantity * specs[good].unit_mass_kg / KILOGRAMS_PER_TONNE for good, quantity in goods.items()
            if good in specs and specs[good].portable and math.isfinite(specs[good].unit_mass_kg)}


def supply_tiles(record, setup, good: GoodId) -> Dict[TileId, float]:
    """Units of `good` a year that each tile's placed producers can make."""
    supply: Dict[TileId, float] = {}
    for producer in sites.in_id_order(record.producers):
        made = setup.recipes[producer.recipe_id].outputs.get(good, 0.0)
        if made > 0.0 and producer.capacity_runs > 0.0:
            supply[producer.tile] = supply.get(producer.tile, 0.0) + producer.capacity_runs * producer.yield_factor * made
    return supply


def mean_haul_cost(carriage, supply: Mapping[TileId, float], tile: TileId) -> float:
    """Carriage per tonne into `tile` from where `supply` is made, weighted by what each tile makes; zero
    when nothing is made (no input to haul is known)."""
    total = math.fsum(supply.values())
    if total <= 0.0:
        return 0.0
    return math.fsum(weight * carriage.cost_per_tonne(source, tile) for source, weight in supply.items()) / total


def input_haul_cost(recipe: Recipe, specs, carriage, supplies: Mapping[GoodId, Mapping[TileId, float]],
                    tile: TileId) -> float:
    """Carriage of one run's inputs into `tile` from where each is made."""
    return math.fsum(tonnes * mean_haul_cost(carriage, supplies.get(good, {}), tile)
                     for good, tonnes in tonnes_of(recipe.inputs, specs).items())


def input_supplies(record, setup, recipe: Recipe, goods=None) -> Dict[GoodId, Dict[TileId, float]]:
    """Where each of the recipe's inputs (or of `goods` among them) is made now."""
    return {good: supply_tiles(record, setup, good) for good in recipe.inputs if goods is None or good in goods}


def fixed_site_goods(recipes: Mapping[str, Recipe], by_limits) -> frozenset:
    """The goods some site-bound recipe with declared limits makes: where they are made is geography's."""
    return frozenset(good for recipe in recipes.values() if sites.is_sited(recipe, by_limits) for good in recipe.outputs)


def fixed_inputs(recipe: Recipe, incumbents: Mapping[GoodId, str], recipes: Mapping[str, Recipe],
                 by_limits) -> Dict[GoodId, str]:
    """The inputs the opening gets from a site-bound recipe with declared limits: input good -> that recipe."""
    fixed = {}
    for good in sorted(recipe.inputs):
        maker = incumbents.get(good)
        if maker is not None and maker != recipe.recipe_id and sites.is_sited(recipes[maker], by_limits):
            fixed[good] = maker
    return fixed


def area_room(record, setup, area_map, good: GoodId, maker: str) -> Dict[str, float]:
    """Units of `good` a year the sited `maker` offers in each market area, less what placed users take."""
    room: Dict[str, float] = {}
    for producer in sites.in_id_order(record.producers):
        recipe = setup.recipes[producer.recipe_id]
        area = area_map.area_of(good, producer.tile)
        if producer.recipe_id == maker:
            room[area] = room.get(area, 0.0) + producer.capacity_runs * producer.yield_factor * recipe.outputs.get(good, 0.0)
        used = recipe.inputs.get(good, 0.0)
        if recipe.plant_life_years > 0.0:
            used += recipe.plant_goods.get(good, 0.0) / recipe.plant_life_years
        if used > 0.0:
            room[area] = room.get(area, 0.0) - producer.capacity_runs * used
    return room


def committed_hours(record, setup) -> Dict[TileId, float]:
    """Hours a year the placed producers of each tile would work at full capacity."""
    hours: Dict[TileId, float] = {}
    for producer in record.producers.values():
        hours[producer.tile] = hours.get(producer.tile, 0.0) + producer.capacity_runs * math.fsum(
            setup.recipes[producer.recipe_id].labour_hours.values())
    return hours


def place_oriented(setup, record, area_map, carriage, recipe: Recipe, fixed: Mapping[GoodId, str],
                   shares: Sequence[Tuple[MarketArea, float]], tiles: Sequence[TileId]) -> Dict[TileId, float]:
    """Runs of capacity for each tile for a processor with fixed-site inputs. `shares` are the runs wanted
    for each market area of its output; `tiles` the tiles it may run on. Only tiles in a market area that
    makes every fixed input can host it. The runs the supply there can feed go to the tiles cheapest first (inputs
    in, output out); the rest of what was wanted is spread over those tiles in the same proportions, so a supply
    that cannot feed the capacity shows as the input's price, not as a smaller opening. Each tile takes no more
    than the hands it can still spare."""
    wanted = math.fsum(runs for _area, runs in shares)
    if wanted <= 0.0:
        return {}
    room = {good: area_room(record, setup, area_map, good, maker) for good, maker in fixed.items()}
    supplies = input_supplies(record, setup, recipe, fixed)
    output_tonnes = math.fsum(tonnes_of(recipe.outputs, setup.specs).values())
    hours_per_run = math.fsum(recipe.labour_hours.values())
    used_hours = committed_hours(record, setup)

    def spare_runs(tile: TileId) -> float:
        if hours_per_run <= 0.0:
            return math.inf
        free = setup.opening_population_by_tile[tile] * setup.working_share * setup.working_hours_per_year - used_hours.get(tile, 0.0)
        return max(0.0, free) / hours_per_run
    costed = []
    for tile in tiles:
        if setup.opening_population_by_tile.get(tile, 0.0) <= 0.0:
            continue
        out_cost = math.fsum(runs * carriage.cost_per_tonne(tile, area.anchor_tile) for area, runs in shares) / wanted
        costed.append((input_haul_cost(recipe, setup.specs, carriage, supplies, tile) + output_tonnes * out_cost, tile))
    fed: Dict[TileId, float] = {}
    left = wanted
    for cost, tile in sorted(costed):
        if left <= 0.0:
            break
        take = min(left, spare_runs(tile))
        for good in fixed:
            take = min(take, room[good].get(area_map.area_of(good, tile), 0.0) / recipe.inputs[good])
        if not (math.isfinite(cost) and take > 0.0):
            continue
        fed[tile] = take
        left -= take
        for good in fixed:
            area = area_map.area_of(good, tile)
            room[good][area] = room[good].get(area, 0.0) - take * recipe.inputs[good]
    total = math.fsum(fed.values())
    if total <= 0.0:
        return {}
    scale = wanted / total
    return dict(sorted((tile, min(runs * scale, spare_runs(tile))) for tile, runs in fed.items()))
