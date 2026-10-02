"""How much more or less households want of each commodity than at the opening.

Households are priced only for goods something offers (`GoodsMarket.household_prices`): a good
nothing offers has no price, so the need it served draws no spending on it.

The household demand model in sim/world/need_demand.py turns population and
income into units wanted per year, through needs, goods and the recipes that
make them. Its absolute quantities do not match the resource tables (it
omits many uses), so the market uses only its change: demand now over demand
at the opening, at the same prices. The society's capacity at the opening is
what built up to meet the opening demand, so that ratio is what moves the
year's price. A commodity the model never reaches follows the whole
economy's size instead.
"""
import copy
import os

from sim.constants import declare
from sim.world import demand, need_demand

MEAN_INCOME_HOURS_PER_CAPITA = declare(
    "MEAN_INCOME_HOURS_PER_CAPITA", 550.0, kind="temporary_heuristic",
    unit="labour-hours/person/year at the opening economy", source=None,
    confidence="D",
    why="Household income scale, the same figure the price solver's demand "
        "anchors use (sim/joint_allocation.py); income then moves with the "
        "economy index. A labour market that reports what households earn "
        "would replace both.")

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


def household_demand_by_material(prices_in_hours, population, income_per_capita):
    """{material: units a year} households (and what they buy through recipes) want."""
    model = copy.copy(_household_model())
    model.bins = demand.income_bins(max(population, 1.0), income_per_capita)
    return model.total_demand(prices_in_hours)


class MarketDemandMixin:
    """Household demand ratios for the engine's yearly market."""

    def _opening_population(self):
        return float(self.civ.get("population", self.DEFAULT_POPULATION_100AD))

    def household_demand_ratios(self):
        """{commodity: demand now over demand at the opening}, from population and today's prices
        against the opening basket (real_output.py); recomputed when the population moves by a
        tenth of a percent or the price table changes."""
        prices = self.goods_market.household_prices()
        key = round(float(self.population.total) / self._opening_population(), 3)
        cache = getattr(self.household, "_household_demand_cache", None)
        if cache is not None and cache[0] == key and cache[1] is prices:
            return cache[2]
        # computed from the rounded key, so the answer depends on the key and not on when it was last computed
        basket = self.base_basket()
        per_hour = self.money_per_labour_hour()
        # only goods households were offered at the opening: a good that appears later has no
        # opening price to value it at, and one only a partner offered is not the home market's
        prices_in_hours = {material: prices[material] / per_hour for material in basket["prices"]
                           if prices.get(material, 0.0) > 0.0}
        now = household_demand_by_material(
            prices_in_hours, key * self._opening_population(), MEAN_INCOME_HOURS_PER_CAPITA)
        opening_by_commodity, now_by_commodity = {}, {}
        for material, units in basket["units"].items():
            commodity = basket["commodity"][material]
            opening_by_commodity[commodity] = opening_by_commodity.get(commodity, 0.0) + units
            now_by_commodity[commodity] = now_by_commodity.get(commodity, 0.0) + now.get(material, 0.0)
        ratios = {commodity: now_by_commodity[commodity] / total
                  for commodity, total in sorted(opening_by_commodity.items()) if total > 0.0}
        self.household._household_demand_cache = (key, prices, ratios)
        return ratios

    def economy_size_ratio(self):
        """Population over the opening's: what demand follows for a commodity the household model
        does not reach."""
        # TEMPORARY HEURISTIC: unreached commodities scale one-for-one with population.
        return float(self.population.total) / self._opening_population()

    def household_demand_ratio(self, commodity):
        ratios = self.household_demand_ratios()
        if commodity in ratios:
            return ratios[commodity]
        return self.economy_size_ratio()
