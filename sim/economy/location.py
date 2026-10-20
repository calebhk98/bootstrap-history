"""Where a recipe is worked inside a market area.

Each tile is its own labour market, so a producer only hires the people of its own tile. At the opening
wages are the same everywhere and a recipe's capacity is spread over the area's tiles by working hours
(by the declared limits for a sited recipe). A newcomer goes to the tile where a run costs least: the
tile's wages, its land rent, the carriage of the run's inputs in from the fixed sites that make them and of
its output to the area's anchor (location_inputs.py), over the site's yield; among the area's tiles and the
tiles holding those fixed sites, with a site and idle hands to staff the run.
"""
import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from . import labour_state, location_inputs, sites, unit_cost
from .market_areas import MarketArea
from .producers import Producer, live_input_prices
from .setup import labour_area
from .types import GoodSpec, Recipe, TileId
from sim.unit_conversions import KILOGRAMS_PER_TONNE


# (recipe id, demand, runs wanted) -> the tile and the runs to build there; None where no tile will do
Siting = Callable[..., Optional[Tuple[TileId, float]]]


@dataclass(frozen=True)
class Candidate:
    tile: TileId
    cost_per_run: float          # money per run per unit of yield, at this tile's prices
    staffable_runs: float        # runs the tile's idle hours could staff
    headroom_runs: float         # runs its site still allows


def split_runs(total: float, weights: Mapping[TileId, float], caps: Mapping[TileId, float]) -> Dict[TileId, float]:
    """`total` shared out by weight, no tile above its cap; what the caps cannot take is dropped."""
    shares = {tile: weight for tile, weight in weights.items() if weight > 0.0}
    result: Dict[TileId, float] = {}
    left = total
    while shares and left > 0.0:
        weight_sum = math.fsum(shares.values())
        capped = {tile for tile, weight in shares.items()
                  if left * weight / weight_sum > caps.get(tile, math.inf) - result.get(tile, 0.0)}
        if not capped:
            for tile, weight in shares.items():
                result[tile] = result.get(tile, 0.0) + left * weight / weight_sum
            break
        for tile in sorted(capped):
            room = caps[tile] - result.get(tile, 0.0)
            result[tile] = result.get(tile, 0.0) + room
            left -= room
            del shares[tile]
    return dict(sorted(result.items()))


def output_tonnes(recipe: Recipe, specs: Mapping[str, GoodSpec]) -> float:
    """Mass of one run's output to carry; a good with nothing to carry adds none."""
    return math.fsum(quantity * specs[good].unit_mass_kg for good, quantity in recipe.outputs.items()
                     if good in specs and specs[good].portable) / KILOGRAMS_PER_TONNE


def cost_per_run(recipe: Recipe, wages: Mapping[str, float], input_prices: Mapping[str, float], rent: float,
                 carriage_per_tonne: float, yield_factor: float, tonnes: float = 0.0, input_haul: float = 0.0) -> float:
    """Variable cost, carriage of a run's output (`tonnes`) to the anchor and of its inputs in (`input_haul`,
    money per run), over the yield."""
    if yield_factor <= 0.0:
        return math.inf
    return assembled_cost(unit_cost.variable_cost_per_run(recipe, input_prices, wages, rent), carriage_per_tonne,
                          yield_factor, tonnes, input_haul)


def assembled_cost(variable: float, carriage_per_tonne: float, yield_factor: float, tonnes: float,
                   input_haul: float) -> float:
    """A run's variable cost plus the carriage of its output and inputs, over the yield (which is positive)."""
    carriage = carriage_per_tonne * tonnes if tonnes > 0.0 else 0.0
    return (variable + carriage + input_haul) / yield_factor


def spare_hours(workforce: Mapping[str, float], working_hours_per_worker: float, committed_hours: float) -> float:
    """Hours the tile's workers could give beyond what its producers already use."""
    return max(0.0, math.fsum(workforce.values()) * working_hours_per_worker - committed_hours)


def staffable_runs(recipe: Recipe, spare: float) -> float:
    hours = math.fsum(recipe.labour_hours.values())
    return math.inf if hours <= 0.0 else spare / hours


def choose(candidates: Sequence[Candidate], runs: float,
           anchor: Optional[TileId] = None) -> Optional[Tuple[Candidate, float]]:
    """The cheapest tile with room that can staff `runs`, else the best staffed; with the runs it takes
    (cut to the staff and the site). Equal costs go to the anchor."""
    open_tiles = [candidate for candidate in candidates if candidate.headroom_runs > 0.0]

    def order(candidate):
        return (candidate.cost_per_run, candidate.tile != anchor, candidate.tile)
    staffed = [candidate for candidate in open_tiles if candidate.staffable_runs >= runs]
    if staffed:
        best = min(staffed, key=order)
    else:
        open_tiles = [candidate for candidate in open_tiles if candidate.staffable_runs > 0.0]
        if not open_tiles:
            return None
        best = max(open_tiles, key=lambda candidate: (candidate.staffable_runs, -candidate.cost_per_run))
    return best, min(runs, best.staffable_runs, best.headroom_runs)


def opening_split(setup, recipe: Recipe, area: MarketArea, runs: float) -> Dict[TileId, float]:
    """A recipe's opening capacity shared over the tiles: by the site limits when sited, else by the
    area's working hours. A site-bound recipe with no declared limit stays at the anchor
    (sites.UNSITED_EXTRACTION_ANYWHERE)."""
    by_recipe = sites.limits_by_recipe(setup.site_limits)
    population = setup.opening_population_by_tile
    suited = tuple(tile for tile in sites.suited_tiles(recipe, setup.tiles, area.tiles, setup.recipe_allowed)
                   if _crops_on(setup, recipe, tile))
    if not suited:
        return {}
    if recipe.site_bound and not by_recipe.get(recipe.recipe_id):
        if area.anchor_tile in suited:
            return {area.anchor_tile: runs}
        return split_runs(runs, {tile: population.get(tile, 0.0) for tile in suited}, {})
    tiles = sites.allowed_tiles(recipe, by_recipe, suited)
    weights = {tile: population.get(tile, 0.0) for tile in tiles}
    if sites.is_sited(recipe, by_recipe):
        limits = by_recipe[recipe.recipe_id]
        weights = {tile: limits[tile].capacity_runs_per_year if population.get(tile, 0.0) > 0.0 else 0.0
                   for tile in limits if setup.recipe_allowed(recipe.recipe_id, tile)}
        local = {tile: weight for tile, weight in weights.items() if tile in area.tiles}
        if math.fsum(local.values()) > 0.0:
            weights = local       # the area's own sites serve it; only an area with none draws on the others
        return split_runs(runs, weights, {tile: limits[tile].capacity_runs_per_year for tile in limits})
    return split_runs(runs, weights, {})


def _crops_on(setup, recipe: Recipe, tile: TileId) -> bool:
    """False where the recipe takes the tile's yield and the tile yields nothing: a run there makes nothing."""
    return setup.yield_factor_by_recipe_tile.get(recipe.recipe_id + "@" + tile, 1.0) > 0.0


def entry_siting(setup, record, view, area_map, carriage) -> Siting:
    """The tile for a newcomer: see `choose`. Each call prices the recipe on every candidate tile."""
    by_recipe = sites.limits_by_recipe(setup.site_limits)
    capacity: Dict[Tuple[str, TileId], float] = {}
    committed: Dict[TileId, float] = {}
    supplies: Dict[str, Mapping] = {}
    tile_parts: Dict[Tuple[str, TileId, float], tuple] = {}    # what a recipe's run on a tile costs apart from the output's carriage
    fixed_goods = location_inputs.fixed_site_goods(setup.recipes, by_recipe)
    for producer in sites.in_id_order(record.producers):
        key = (producer.recipe_id, producer.tile)
        capacity[key] = capacity.get(key, 0.0) + producer.capacity_runs + record.expansion_runs.get(producer.agent_id, 0.0)
        recipe = setup.recipes[producer.recipe_id]
        working = producer.capacity_runs if producer.last_runs < 0.0 else producer.last_runs
        committed[producer.tile] = committed.get(producer.tile, 0.0) + working * math.fsum(recipe.labour_hours.values())

    def siting(recipe_id, demand, runs):
        recipe = setup.recipes[recipe_id]
        area = area_map.market_area_of(demand.good, demand.anchor_tile)
        if recipe.site_bound and not by_recipe.get(recipe_id) and sites.climate_allows(
                recipe, setup.tiles.get(demand.anchor_tile)) and setup.recipe_allowed(recipe_id, demand.anchor_tile):
            return demand.anchor_tile, runs
        tonnes = output_tonnes(recipe, setup.specs)
        if recipe_id not in supplies:
            supplies[recipe_id] = location_inputs.input_supplies(record, setup, recipe, fixed_goods)
        candidates: List[Candidate] = []
        reachable = tuple(setup.tiles) if sites.is_sited(recipe, by_recipe) else tuple(sorted(
            set(area.tiles) | {tile for supply in supplies[recipe_id].values() for tile in supply}))
        for tile in sites.suited_tiles(recipe, setup.tiles, sites.allowed_tiles(recipe, by_recipe, reachable),
                                       setup.recipe_allowed):
            fixed_part = tile_parts.get((recipe_id, tile, carriage.scale))
            if fixed_part is None:
                fixed_part = tile_parts[(recipe_id, tile, carriage.scale)] = _tile_part(
                    setup, record, view, carriage, recipe, by_recipe, supplies[recipe_id], capacity, committed, tile)
            variable, factor, input_haul, staffable, headroom = fixed_part
            cost = math.inf if factor <= 0.0 else assembled_cost(
                variable, carriage.cost_per_tonne(tile, demand.anchor_tile), factor, tonnes, input_haul)
            candidates.append(Candidate(tile, cost, staffable, headroom))
        picked = choose(candidates, runs, demand.anchor_tile)
        return None if picked is None else (picked[0].tile, picked[1])
    return siting


def _tile_part(setup, record, view, carriage, recipe, by_recipe, supplies, capacity, committed, tile):
    """(variable cost per run, yield factor, input haul per run, staffable runs, headroom runs) of `recipe` on
    `tile`: none of it depends on where the output goes, so one entry-siting call reads it once per recipe and tile."""
    probe = Producer("probe", "probe", recipe.recipe_id, tile, 1.0)
    factor = sites.yield_at(recipe, tile, by_recipe, setup.yield_factor_by_recipe_tile.get(
        recipe.recipe_id + "@" + tile, 1.0))
    variable = None
    if factor > 0.0:
        wages = {trade: _wage(setup, view, trade, tile) for trade in recipe.labour_hours}
        variable = unit_cost.variable_cost_per_run(
            recipe, live_input_prices(probe, recipe, view), wages,
            record.land_rent.get(tile, 0.0) * setup.land_per_run.get(recipe.recipe_id, 0.0))
    input_haul = location_inputs.input_haul_cost(recipe, setup.specs, carriage, supplies, tile)
    spare = spare_hours(labour_state.people_by_trade(record.workforce, labour_area(tile)), setup.working_hours_per_year,
                        committed.get(tile, 0.0))
    return (variable, factor, input_haul, staffable_runs(recipe, spare),
            sites.headroom_runs(recipe, tile, by_recipe, capacity.get((recipe.recipe_id, tile), 0.0)))


def _wage(setup, view, trade, tile) -> float:
    wage = view.wage(trade, labour_area(tile))
    return setup.opening_wages.get(trade, math.inf) if wage is None else wage
