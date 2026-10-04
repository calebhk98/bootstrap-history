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

from . import goods_market_offers

MEAN_INCOME_HOURS_PER_CAPITA = declare(
    "MEAN_INCOME_HOURS_PER_CAPITA", 550.0, kind="temporary_heuristic",
    unit="labour-hours/person/year at the opening economy", source=None,
    confidence="D",
    why="Household income scale, the same figure the price solver's demand "
        "anchors use (sim/engine/joint_allocation.py); income then moves with the "
        "wage the labour market pays (household_income_hours_per_capita). Returns to land and capital "
        "are not yet in it.")

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

    def household_income_hours_per_capita(self):
        """Labour hours a person earns a year: the opening's income, carried by what an hour of the
        unskilled trade pays now against the opening (the labour market's scarcity of hands and the
        share of output gain it passes on). Prices here are the solver's own, so cost of living and
        the price level are left out of the wage. Returns to land and capital are not yet in it."""
        # TEMPORARY HEURISTIC: every household earns the mean; the spread and the returns are not modelled.
        return MEAN_INCOME_HOURS_PER_CAPITA * self.labour.market.household_wage_ratio()

    def household_real_income_ratio(self):
        """What a person's income buys of the opening basket now over what it bought at the opening:
        income in hours over the opening's, over the basket's cost at today's prices against its cost then."""
        basket = self.base_basket()
        prices = self.goods_market.household_prices()
        per_hour = self.labour.money_per_labour_hour()
        opening_cost = now_cost = 0.0
        for material, units in basket["units"].items():
            if prices.get(material, 0.0) > 0.0:
                opening_cost += units * basket["prices"][material]
                now_cost += units * prices[material] / per_hour
        if opening_cost <= 0.0 or now_cost <= 0.0:
            return 1.0
        return self.household_income_hours_per_capita() / MEAN_INCOME_HOURS_PER_CAPITA * opening_cost / now_cost

    def household_demand_ratios(self):
        """{commodity: demand now over demand at the opening}, from population, income and today's
        prices against the opening basket (real_output.py); recomputed when the population or the wage
        moves by a tenth of a percent or the price table changes."""
        return self._household_demand_now()[0]

    def household_new_goods_units(self):
        """{material: units a year households want} of goods offered now that the opening did not offer."""
        return self._household_demand_now()[1]

    def _household_demand_now(self):
        prices = self.goods_market.household_prices()
        key = (round(float(self.population.total) / self._opening_population(), 3),
               round(self.household_income_hours_per_capita(), 3))
        cache = getattr(self.household, "_household_demand_cache", None)
        if cache is not None and cache[0] == key and cache[1] is prices:
            return cache[2], cache[3]
        # computed from the rounded key, so the answer depends on the key and not on when it was last computed
        basket = self.base_basket()
        per_hour = self.labour.money_per_labour_hour()
        # the opening's goods and any the home society now makes, so a need a new good serves can turn to
        # it; a good only a partner offers is not the home market's
        seller_at_home = goods_market_offers.HOME_SELLER
        prices_in_hours = {material: price / per_hour for material, price in prices.items()
                           if price > 0.0 and (material in basket["prices"]
                                               or self.goods_market.offered_by(material) == seller_at_home)}
        now = household_demand_by_material(prices_in_hours, key[0] * self._opening_population(), key[1])
        opening_by_commodity, now_by_commodity = {}, {}
        for material, units in basket["units"].items():
            commodity = basket["commodity"][material]
            opening_by_commodity[commodity] = opening_by_commodity.get(commodity, 0.0) + units
            now_by_commodity[commodity] = now_by_commodity.get(commodity, 0.0) + now.get(material, 0.0)
        ratios = {commodity: now_by_commodity[commodity] / total
                  for commodity, total in sorted(opening_by_commodity.items()) if total > 0.0}
        new_units = {material: wanted for material, wanted in sorted(now.items())
                     if wanted > 0.0 and material not in basket["units"]}
        self.household._household_demand_cache = (key, prices, ratios, new_units)
        return ratios, new_units

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
