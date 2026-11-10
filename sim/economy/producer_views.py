"""What other packages read of the producers, as lists made from the producer table's columns (no `Producer` is built).

`producer_list(economy, scoped)` is the producers in id order: their ids, recipes, tiles, capacity and last year's runs as parallel
lists. With `scoped` the producers are those working on the home country's tiles when the economy holds several countries (as
`api.producers_of` says), else every producer. `capacity_units_by_material(economy)` adds each producer's capacity times what its recipe
makes, in id order, and is kept while the table is unchanged."""
from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from . import country_figures


@dataclass(frozen=True)
class ProducerList:
    ids: List[str]
    recipe_ids: List[str]
    tiles: List[str]
    capacity_runs: List[float]
    last_runs: List[float]


def producer_list(economy, scoped: bool = True) -> ProducerList:
    """The producers (the home country's when `scoped`) by id."""
    store = economy.record.producers
    rows = store.order()
    if scoped:
        scope = country_figures.home_when_shared(economy, None)
        if scope is not None:
            tiles = country_figures.country_tiles(economy, scope)
            names = store.names["tiles"].name_list
            inside = np.array([name in tiles for name in names], dtype=np.bool_)
            rows = rows[inside[store.table.tile[rows]]]
    table = store.table
    return ProducerList([store.ids[row] for row in rows.tolist()], store.name_of("recipes", table.recipe[rows]),
                        store.name_of("tiles", table.tile[rows]), store.floats("capacity_runs", rows), store.floats("last_runs", rows))


_units_kept: Dict[int, tuple] = {}      # id of a producer table -> (table, its version, the recipes, the units by material)


def capacity_units_by_material(economy) -> Dict[str, float]:
    """Units a year of each material the home country's producers can make at full capacity, summed in id order."""
    store, recipes = economy.record.producers, economy.setup.recipes
    kept = _units_kept.get(id(store))
    if kept is not None and kept[0] is store and kept[1] == store.version and kept[2] is recipes:
        return kept[3]
    listed = producer_list(economy)
    units: Dict[str, float] = {}
    for recipe_id, capacity in zip(listed.recipe_ids, listed.capacity_runs):
        recipe = recipes.get(recipe_id)
        if recipe is not None:
            for material, quantity in recipe.outputs.items():
                units[material] = units.get(material, 0.0) + capacity * quantity
    _units_kept[id(store)] = (store, store.version, recipes, units)
    return units
