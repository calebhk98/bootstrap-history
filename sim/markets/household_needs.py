"""The household need model's rules: units of each material households want a year at given prices, population and income.

The model (sim/world/need_demand.py) turns population and income into units wanted per year, through needs, goods and the
recipes that make them; its absolute quantities do not match the resource tables (it omits many uses). The module builds it from
the installed content's need data (the `household_need_data` view) once per set of installed mods, and these functions are
what its views call. The model and the climate baskets are remembered for the process, keyed on what they were built from."""
import copy

from sim.geography.api import layer_value, settlement, tiles_held
from sim.world import demand, need_basket, need_demand
from sim.world.material_units import tonnes_per_unit

from .constants import MEAN_INCOME_HOURS_PER_CAPITA

_MODELS = {}             # installed mod ids -> (the need-demand model, the goods households buy for themselves)
_CLIMATE_BASKETS = {}    # civilisation id -> (the map, the basket built on it, the model)


def household_model(mod_ids, load_need_data):
	"""(the need-demand model, the final goods) for the installed content, built once per process and per set of installed
	mods (its population is replaced on each use). `load_need_data()` returns {"needs", "goods"} and is called only on a miss."""
	built = _MODELS.get(mod_ids)
	if built is None:
		needs = load_need_data()
		bins = demand.income_bins(1.0, MEAN_INCOME_HOURS_PER_CAPITA)
		model = need_demand.NeedDemandModel(needs, demand.production_data(), bins, satiate=True)
		built = _MODELS[mod_ids] = (model, frozenset(needs["goods"]))
	return built


def climate_records(civ, world_map):
	"""[(a tile's climate record, its share of the opening population)] for the tiles the civilisation holds."""
	tile_ids = tiles_held(civ, world_map)
	return [({"lat": layer_value(tile, "lat", world_map),
	          "koppen_class": layer_value(tile, "koppen_class", world_map),
	          "koppen_sample_mix": layer_value(tile, "koppen_sample_mix", world_map)},
	         settlement.population_share(tile_ids, tile)) for tile in tile_ids]


def civilisation_basket(model, civ, world_map):
	"""The model's basket with the floors the climate of the civilisation's tiles sets, each tile weighted by its share of
	the opening population (remembered for the map it was built on)."""
	key = str(civ["id"])
	cached = _CLIMATE_BASKETS.get(key)
	if cached is not None and cached[0] is world_map and cached[2] is model:
		return cached[1]
	basket = need_basket.mean_climate_basket(model.basket, climate_records(civ, world_map))
	_CLIMATE_BASKETS[key] = (world_map, basket, model)
	return basket


def demand_by_material(base, prices_in_hours, population, income_per_capita, basket=None):
	"""{material: units a year} households (and what they buy through recipes) want. With `basket` (a civilisation's, from
	civilisation_basket) the warmth, clothing and shelter floors are those its tiles' climate sets."""
	model = copy.copy(base)
	model.bins = demand.income_bins(max(population, 1.0), income_per_capita)
	if basket is not None:
		model.basket = basket
	return model.total_demand(prices_in_hours)


def budget_scaled_final_tonnes(units, prices_in_hours, population, final_goods):
	"""{material: tonnes a year} households buy for themselves of the `units` a year the model gives at these prices (labour
	hours a unit), scaled down uniformly when the spending exceeds the income they have. Goods bought as inputs to other goods are
	left out: the model's levels for those are not credible."""
	spending = sum(quantity * prices_in_hours.get(material, 0.0)
	               for material, quantity in units.items())
	income = population * MEAN_INCOME_HOURS_PER_CAPITA
	scale = min(1.0, income / spending) if spending > 0.0 else 1.0
	return {material: quantity * scale * tonnes_per_unit(material)
	        for material, quantity in units.items() if material in final_goods}
