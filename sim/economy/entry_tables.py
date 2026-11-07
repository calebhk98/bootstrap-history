"""The year's entry costing over the year arrays: the tables the entry kernels (entry_kernels.py) read, built once when the
year's entry opens, and the calls the entry rules make of them.

`EntryTables.build(setup, record, view, area_map, arrays, carriage, crews_of)` packs, from the synced year arrays, the prices
on every tile, the wages, the recipes' matrices, the land rents, the carriage between tiles, what each tile's producers make
and the hands each has to spare. The rules (entry.py, entry_margin.py, entry_trial.py, entry_backed.py, location.py) ask it
for the cost of a recipe on a tile, a recipe's return on capital, or a tile for a newcomer; each call is the same rule as the
function it stands in for, which stays as the plain path (a caller with no tables). A recipe's own reads (its entrant's
practice, the tiles it may be placed on, its yield and limit on each) are made the first time a request names it.
Built inside `entry_practice.shared_crews`, whose grouping of producers by recipe `crews_of` reads."""
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from sim.labour.api import SOURCE_TASK_FLOOR_FRACTION, learning_curve

from . import entry_kernels, labour_state, location, location_inputs, practice, sites
from .entry_spare import idle_runs
from .location_land import land_short_tiles
from .producers_close import LOSS_YEARS_BEFORE_EXIT
from .rates import own_rate
from .setup import labour_area, recipe_tile_key
from .types import TileId
from .year_arrays_memory import NO_AREA

NO_ROW = -1


@dataclass
class RecipeSite:
    """What siting reads of one recipe, worked out the first time it is sited."""
    sited: bool
    runs_anywhere: bool
    suited: np.ndarray            # tile rows where its climate and its people allow it and a limit (if sited) is declared
    fits: np.ndarray              # tile rows where its climate and its people allow it
    order: Optional[np.ndarray]   # sited: the suited tile rows in the setup's tile order, else None
    supply_tiles: np.ndarray      # tile rows where a maker of a fixed-site input stands
    tonnes_out: float
    hours_per_run: float          # the hours of a run in an entrant's first year


class EntryTables:
    def __init__(self, setup, record, view, area_map, arrays, carriage, crews_of):
        self.setup, self.record, self.area_map, self.arrays = setup, record, area_map, arrays
        self.carriage, self.crews_of = carriage, crews_of
        matrices, memory = arrays.matrices, arrays.memory
        self.matrices, self.tiles, self.goods, self.trades = matrices, arrays.tiles, matrices.goods, matrices.trades
        self.recipe_row = matrices.recipes.row
        self.own_rate = own_rate(view, setup.currency_id)
        goods_count, tile_count = len(self.goods.ids), len(self.tiles.ids)
        columns = arrays.area_index.of_good_tile
        found = columns != NO_AREA
        safe = np.where(found, columns, 0)
        rows = np.arange(goods_count)[:, None]
        if memory.price.shape[1]:
            remembered = np.where(found, memory.price[rows, safe], np.nan)
            offered = np.where(found, memory.offered[rows, safe], np.nan)
        else:
            remembered = offered = np.full((goods_count, tile_count), np.nan)
        price = np.ascontiguousarray(np.stack([remembered.T, offered.T]))
        recipe_ids = matrices.recipes.ids
        recipe_scalar = np.array([[matrices.plant_life_years[row], setup.land_per_run.get(recipe_id, 0.0)]
                                  for row, recipe_id in enumerate(recipe_ids)], dtype=np.float64).reshape(len(recipe_ids), 2)
        tile_scalar = np.array([[record.land.land_rent.get(tile, 0.0), record.land.land_mean_value.get(tile, 0.0)]
                                for tile in self.tiles.ids], dtype=np.float64).reshape(tile_count, 2)
        self.start_units = np.full((len(recipe_ids), len(self.trades.ids)), practice.established_units())
        self.curve = np.array([learning_curve.learning_exponent(learning_curve.LEARNING_RATE), SOURCE_TASK_FLOOR_FRACTION,
                               float(max(1, LOSS_YEARS_BEFORE_EXIT))])
        self.tables = (np.ascontiguousarray(np.stack([matrices.inputs, matrices.outputs, matrices.plant_goods])),
                       np.ascontiguousarray(np.stack([matrices.labour_hours, matrices.plant_labour_hours])),
                       matrices.slot_goods, matrices.slot_trades, price, np.ascontiguousarray(memory.wage.T),
                       recipe_scalar, tile_scalar, self.start_units, self.curve)
        self._crew_ready = np.zeros(len(recipe_ids), dtype=np.bool_)
        self._first_hours = np.zeros(len(recipe_ids))
        self._sites: Dict[int, RecipeSite] = {}
        self._siting_ready = False
        self._area_masks: Dict[str, np.ndarray] = {}

    @classmethod
    def build(cls, setup, record, view, area_map, arrays, carriage, crews_of) -> "EntryTables":
        return cls(setup, record, view, area_map, arrays, carriage, crews_of)

    # ---- costs -------------------------------------------------------------------------------------------------
    def _ensure_crew(self, row: int) -> None:
        """The practice an entrant of the recipe starts at, and the hours of its first year's run."""
        if self._crew_ready[row]:
            return
        recipe_id = self.matrices.recipes.ids[row]
        recipe = self.setup.recipes[recipe_id]
        crew = self.crew_of(recipe)
        for trade, units in crew.items():
            self.start_units[row, self.trades.row[trade]] = units
        self._first_hours[row] = math.fsum(practice.recipe_for(recipe, crew).labour_hours.values())
        self._crew_ready[row] = True

    def crew_of(self, recipe) -> Dict[str, float]:
        from . import entry_practice
        return entry_practice.entrant_crew(recipe, self.crews_of(recipe.recipe_id))

    def recipes_by_cost_many(self, requests: Sequence[Tuple[str, TileId, Sequence[str], Optional[float]]]
                             ) -> List[List[Tuple[str, float]]]:
        """`entry_trial.recipes_by_cost` for each (good, tile, recipe ids, output a year or None), cheapest first."""
        recipe_rows, tile_rows, good_cols, runs, owner = [], [], [], [], []
        for index, (good, tile, recipe_ids, output_per_year) in enumerate(requests):
            good_col, tile_row = self.goods.row[good], self.tiles.row[tile]
            for recipe_id in recipe_ids:
                row = self.recipe_row[recipe_id]
                made = self.setup.recipes[recipe_id].outputs.get(good, 0.0)
                planned = output_per_year is not None and made > 0.0
                if planned:
                    self._ensure_crew(row)
                recipe_rows.append(row)
                tile_rows.append(tile_row)
                good_cols.append(good_col)
                runs.append(output_per_year / made if planned else math.nan)
                owner.append(index)
        costs = entry_kernels.full_costs(np.array(recipe_rows, dtype=np.int64), np.array(tile_rows, dtype=np.int64),
                                         np.array(good_cols, dtype=np.int64), np.array(runs, dtype=np.float64),
                                         self.own_rate, self.tables).tolist()
        ranked: List[List[Tuple[str, float]]] = [[] for _request in requests]
        recipe_ids_of = self.matrices.recipes.ids
        for cost, row, index in zip(costs, recipe_rows, owner):
            if math.isfinite(cost) and cost > 0.0:
                ranked[index].append((recipe_ids_of[row], cost))
        return [sorted(each, key=lambda item: (item[1], item[0])) for each in ranked]

    def recipes_by_cost(self, good, tile, recipe_ids, output_per_year=None) -> List[Tuple[str, float]]:
        """`recipes_by_cost_many` for one request, each recipe costed by a call of its own."""
        good_col, tile_row = self.goods.row[good], self.tiles.row[tile]
        found = []
        for recipe_id in recipe_ids:
            row = self.recipe_row[recipe_id]
            made = self.setup.recipes[recipe_id].outputs.get(good, 0.0)
            planned = output_per_year is not None and made > 0.0
            if planned:
                self._ensure_crew(row)
            cost = entry_kernels.full_cost_one(row, tile_row, good_col, output_per_year / made if planned else math.nan,
                                               self.own_rate, self.tables)
            if math.isfinite(cost) and cost > 0.0:
                found.append((recipe_id, cost))
        return sorted(found, key=lambda item: (item[1], item[0]))

    def returns_many(self, requests: Sequence[Tuple[str, TileId, Optional[float], float]]
                     ) -> List[Tuple[Optional[float], Optional[float]]]:
        """`entry._returns_at` for each (recipe id, tile, runs a year the entrant's hours are planned on or None for the booked
        hours, the market rate): (yearly return, return after the plant's wear), None where it cannot be worked out."""
        rows = np.array([self.recipe_row[each[0]] for each in requests], dtype=np.int64)
        tiles = np.array([self.tiles.row[each[1]] for each in requests], dtype=np.int64)
        runs = np.array([math.nan if each[2] is None else each[2] for each in requests], dtype=np.float64)
        for row, planned in zip(rows.tolist(), runs.tolist()):
            if not math.isnan(planned):
                self._ensure_crew(row)
        gross, after = entry_kernels.returns_many(rows, tiles, runs, np.array([each[3] for each in requests], dtype=np.float64),
                                                  self.tables)
        return [(None if math.isnan(first) else first, None if math.isnan(second) else second)
                for first, second in zip(gross.tolist(), after.tolist())]

    def _pending(self) -> np.ndarray:
        """The plant runs still to come, by producer row."""
        columns = self.arrays.producers
        pending = np.zeros(len(columns.ids))
        for producer_id, runs in self.record.credit.expansion_runs.items():
            row = columns.row.get(producer_id)
            if row is not None:
                pending[row] = runs
        return pending

    def capacity_in(self):
        """`f(good, area id)`: the output the makers in the market could reach (`entry_trial.capacity_in_area` of
        `capacity_terms_by_good`), plant to come counted."""
        columns = self.arrays.producers
        index = self.arrays.area_index
        reach = entry_kernels.reach_by_area(columns.recipe_row, columns.tile_row, columns.capacity_runs, columns.yield_factor,
                                            self._pending(), self.matrices.outputs, index.of_good_tile, len(index.areas.ids))
        goods_row, areas_row = self.goods.row, index.areas.row

        def capacity(good, area_id):
            good_column, area_column = goods_row.get(good), areas_row.get(area_id)
            return 0.0 if good_column is None or area_column is None else float(reach[good_column, area_column])
        return capacity

    # ---- spare output -----------------------------------------------------------------------------------------
    def spare_output(self) -> np.ndarray:
        """`entry_year._spare_output` as a grid over good column and area column."""
        columns = self.arrays.producers
        return entry_kernels.idle_output(columns.recipe_row, columns.tile_row, columns.capacity_runs, columns.last_runs, self._pending(),
                                         columns.land_run_cap, columns.yield_factor, self.matrices.outputs,
                                         self.arrays.area_index.of_good_tile, len(self.arrays.area_index.areas.ids))

    # ---- siting -----------------------------------------------------------------------------------------------
    def _ready_siting(self) -> None:
        """What every siting reads of the producers and the map; read once, on the first siting."""
        setup, record, columns = self.setup, self.record, self.arrays.producers
        matrices = self.matrices
        tile_count, goods_count = len(self.tiles.ids), len(self.goods.ids)
        self.by_recipe = sites.limits_by_recipe(setup.site_limits)
        climates = [getattr(setup.tiles.get(tile), "climate_class", "") if setup.tiles.get(tile) is not None else "" for tile in self.tiles.ids]
        self.climate_codes = {name: code for code, name in enumerate(sorted({each for each in climates if each}))}
        self.climate_of_tile = np.array([self.climate_codes.get(each, -1) for each in climates], dtype=np.int64)
        if hasattr(setup, "country_of"):
            of_tile = [setup.country_of(tile) for tile in self.tiles.ids]
            self.countries = sorted(set(of_tile))
            self.country_of_tile = np.array([self.countries.index(each) for each in of_tile], dtype=np.int64)
        fixed = location_inputs.fixed_site_goods(setup.recipes, self.by_recipe)
        self.fixed_goods = np.array([good in fixed for good in self.goods.ids], dtype=np.bool_)
        pending = self._pending()
        self.capacity = np.zeros((len(matrices.recipes.ids), tile_count))
        np.add.at(self.capacity, (columns.recipe_row, columns.tile_row), columns.capacity_runs + pending)
        self.committed = np.zeros(tile_count)
        booked_hours = {}
        for position, producer in enumerate(columns.records):
            recipe = setup.recipes[producer.recipe_id]
            hours = booked_hours.get(producer.recipe_id) if not producer.crew_runs else None
            if hours is None:
                hours = math.fsum(practice.recipe_for(recipe, producer.crew_runs).labour_hours.values())
                if not producer.crew_runs:
                    booked_hours[producer.recipe_id] = hours
            working = producer.capacity_runs if producer.last_runs < 0.0 else producer.last_runs
            self.committed[columns.tile_row[position]] += working * hours
        self.short_of_land = np.zeros(tile_count, dtype=np.bool_)
        for tile in land_short_tiles((each.tile, each.land_run_cap, setup.land_per_run.get(each.recipe_id, 0.0) > 0.0)
                                     for each in columns.records):
            self.short_of_land[self.tiles.row[tile]] = True
        self.supply_weight, self.supply_present = entry_kernels.supply_by_tile(
            columns.recipe_row, columns.tile_row, columns.capacity_runs, columns.yield_factor, matrices.outputs, tile_count)
        self.hands_hours = np.array([math.fsum(labour_state.people_by_trade(record.labour.workforce, labour_area(tile)).values())
                                     for tile in self.tiles.ids]) * setup.working_hours_per_year
        carriage = np.full((tile_count, tile_count), np.inf)
        for source in self.tiles.ids:
            reached = self.carriage.costs_from(source) if hasattr(self.carriage, "costs_from") else {
                tile: self.carriage.cost_per_tonne(source, tile) for tile in self.tiles.ids}
            for tile, cost in reached.items():
                column = self.tiles.row.get(tile)
                if column is not None:
                    carriage[self.tiles.row[source], column] = cost
        self.carriage_matrix = carriage
        recipe_count = len(matrices.recipes.ids)
        self.yield_rt = np.ones((recipe_count, tile_count))
        self.limit_rt = np.full((recipe_count, tile_count), np.inf)
        self.hauls = np.full((recipe_count, tile_count), np.nan)
        self.input_tonnes = np.zeros((recipe_count, goods_count))
        self._siting_ready = True

    def _site_of(self, row: int) -> RecipeSite:
        kept = self._sites.get(row)
        if kept is not None:
            return kept
        setup, matrices = self.setup, self.matrices
        recipe_id = matrices.recipes.ids[row]
        recipe = setup.recipes[recipe_id]
        self._ensure_crew(row)
        sited, anywhere = sites.is_sited(recipe, self.by_recipe), sites.runs_anywhere(recipe, self.by_recipe)
        tile_ids = self.tiles.ids
        fits = self._allowed_by_climate(recipe) & self._allowed_by_people(recipe_id)
        limits = self.by_recipe.get(recipe_id, {})
        suited = fits & np.array([tile in limits for tile in tile_ids], dtype=np.bool_) if sited else fits
        for column, tile in enumerate(tile_ids):
            self.yield_rt[row, column] = sites.yield_at(recipe, tile, self.by_recipe, setup.yield_factor_by_recipe_tile.get(
                recipe_tile_key(recipe_id, tile), 1.0))
            if sited:
                self.limit_rt[row, column] = limits[tile].capacity_runs_per_year if tile in limits else 0.0
        for good, tonnes in location_inputs.tonnes_of(recipe.inputs, setup.specs).items():
            if self.fixed_goods[self.goods.row[good]]:
                self.input_tonnes[row, self.goods.row[good]] = tonnes
        order = None
        if sited:
            order = np.array([self.tiles.row[tile] for tile in setup.tiles if tile in self.tiles.row and suited[self.tiles.row[tile]]],
                             dtype=np.int64)
        supplied = np.zeros(len(tile_ids), dtype=np.bool_)
        for good in recipe.inputs:
            if self.fixed_goods[self.goods.row[good]]:
                supplied |= self.supply_present[self.goods.row[good]]
        found = RecipeSite(sited, anywhere, suited, fits, order, supplied, location.output_tonnes(recipe, setup.specs),
                           float(self._first_hours[row]))
        self._sites[row] = found
        return found

    def _allowed_by_climate(self, recipe) -> np.ndarray:
        """`sites.climate_allows` on every tile."""
        classes = recipe.climate_classes
        if not classes:
            return np.ones(len(self.tiles.ids), dtype=np.bool_)
        wanted = [self.climate_codes[each] for each in classes if each in self.climate_codes]
        return (self.climate_of_tile < 0) | np.isin(self.climate_of_tile, wanted)

    def _allowed_by_people(self, recipe_id: str) -> np.ndarray:
        """`setup.recipe_allowed` on every tile: the techniques of the tile's country allow the recipe."""
        setup = self.setup
        by_country = getattr(setup, "recipes_by_country", None)
        if by_country is None or not hasattr(setup, "country_of"):
            return np.array([setup.recipe_allowed(recipe_id, tile) for tile in self.tiles.ids], dtype=np.bool_)
        if not by_country:
            return np.ones(len(self.tiles.ids), dtype=np.bool_)
        return np.array([recipe_id in by_country.get(country, ()) for country in self.countries], dtype=np.bool_)[self.country_of_tile]

    def _area_mask(self, area) -> np.ndarray:
        mask = self._area_masks.get(area.area_id)
        if mask is None:
            mask = np.zeros(len(self.tiles.ids), dtype=np.bool_)
            for tile in area.tiles:
                row = self.tiles.row.get(tile)
                if row is not None:
                    mask[row] = True
            self._area_masks[area.area_id] = mask
        return mask

    def siting(self):
        """`location.entry_siting`'s function over these tables: (recipe id, demand, runs wanted) -> (tile, runs) or None."""
        self._ready_siting()
        setup = self.setup

        def siting(recipe_id, demand, runs):
            row = self.recipe_row[recipe_id]
            site = self._site_of(row)
            anchor = self.tiles.row[demand.anchor_tile]
            takes_land = self.tables[6][row, 1] > 0.0
            if site.runs_anywhere and not (takes_land and self.short_of_land[anchor]) and site.fits[anchor]:
                self.capacity[row, anchor] += runs
                self.committed[anchor] += runs * site.hours_per_run
                return demand.anchor_tile, runs
            if site.sited:
                candidates = site.order
            else:
                area = self.area_map.market_area_of(demand.good, demand.anchor_tile)
                candidates = np.flatnonzero(site.suited & (self._area_mask(area) | site.supply_tiles))
            tile, taken = entry_kernels.site_choice(
                row, anchor, candidates, runs, site.tonnes_out, self.tables, self.input_tonnes, self.supply_weight,
                self.supply_present, self.carriage_matrix, self.hauls, self.yield_rt, self.limit_rt, bool(takes_land),
                self.short_of_land, self.hands_hours, self.capacity, self.committed, site.hours_per_run)
            return None if tile < 0 else (self.tiles.ids[tile], taken)
        return siting
