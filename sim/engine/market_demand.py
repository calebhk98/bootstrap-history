"""The household need model: units of each material households want a year at given prices, population and income.

The markets module turns its change from the opening into the year's demand ratios (sim/markets/demand.py) and reads this
model through the `household_demand_units` view (bridge_markets.py); the partner economies' demand (partner_demand.py) calls it
directly. The model in sim/world/need_demand.py turns population and income into units wanted per year, through needs, goods
and the recipes that make them; its absolute quantities do not match the resource tables (it omits many uses)."""
import copy
import os

from sim.geography.api import layer_value, settlement, tiles_held
from sim.world import demand, need_basket, need_demand

from sim.markets.api import MEAN_INCOME_HOURS_PER_CAPITA

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MODEL_CACHE = {}


def _household_model():
    """The need-demand model for the installed content, built once per process
    and per set of installed mods (its population is replaced on each use)."""
    from . import need_data
    from .mods import get_ordered_mods
    mods = tuple(manifest.id for manifest in get_ordered_mods(os.path.join(_REPO_ROOT, "mods")))
    model = _MODEL_CACHE.get(mods)
    if model is None:
        needs = need_data.load_needs(_REPO_ROOT)
        bins = demand.income_bins(1.0, MEAN_INCOME_HOURS_PER_CAPITA)
        model = _MODEL_CACHE[mods] = need_demand.NeedDemandModel(
            needs, demand.production_data(), bins, satiate=True)
    return model


_CLIMATE_BASKETS = {}


def climate_records(civ, world_map):
    """[(a tile's climate record, its share of the opening population)] for the tiles the civilisation holds."""
    tile_ids = tiles_held(civ, world_map)
    return [({"lat": layer_value(tile, "lat", world_map),
              "koppen_class": layer_value(tile, "koppen_class", world_map),
              "koppen_sample_mix": layer_value(tile, "koppen_sample_mix", world_map)},
             settlement.population_share(tile_ids, tile)) for tile in tile_ids]


def _civilisation_basket(model, civ, world_map):
    """The model's basket with the floors the climate of the civilisation's tiles sets, each tile
    weighted by its share of the opening population (cached for the map it was built on)."""
    key = str(civ["id"])
    cached = _CLIMATE_BASKETS.get(key)
    if cached is not None and cached[0] is world_map and cached[2] is model:
        return cached[1]
    basket = need_basket.mean_climate_basket(model.basket, climate_records(civ, world_map))
    _CLIMATE_BASKETS[key] = (world_map, basket, model)
    return basket


def household_basket(civ, world_map):
    """The household need basket of a civilisation: the installed content's needs with the floors its
    tiles' climate sets."""
    return _civilisation_basket(_household_model(), civ, world_map)


def household_demand_by_material(prices_in_hours, population, income_per_capita, civ=None, world_map=None):
    """{material: units a year} households (and what they buy through recipes) want. With a
    civilisation and its map, the warmth, clothing and shelter floors are those its tiles' climate sets."""
    base = _household_model()
    model = copy.copy(base)
    model.bins = demand.income_bins(max(population, 1.0), income_per_capita)
    if civ is not None and world_map is not None:
        model.basket = _civilisation_basket(base, civ, world_map)
    return model.total_demand(prices_in_hours)
