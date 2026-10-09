"""What a foreign economy produces and wants, from its own society.

Demand is its own households' purchases of final goods (its population and
income at its own solved prices, the household model the home market uses for
its ratios), held to the income they have; goods bought only as inputs to
other goods are not traded until an industrial demand model prices them. Capacity is what its own tiles and recipes can supply: a
mined commodity follows the shares of the deposits on its tiles; a made or grown one
follows its demand when the economy holds a technique for every step of the
chain and every ore deposit on that chain lies on its tiles; anything else
has no capacity and is only bought.
"""
import functools

from sim.constants import declare
from sim.geography.api import tiles_held
from sim.world import demand as demand_model

from .data import ROOT, load_civ, starting_schedule
from .market_demand import MEAN_INCOME_HOURS_PER_CAPITA, household_demand_by_material
from .material_units import tonnes_per_unit

FOREIGN_OPENING_IN_BALANCE = declare(
    "FOREIGN_OPENING_IN_BALANCE", 1.0, kind="temporary_heuristic",
    unit="foreign capacity over foreign demand for a good it can make",
    source=None, confidence="D",
    why="A foreign economy's made or grown goods open with its capacity "
        "equal to its households' demand, so its own market is in balance "
        "until trade moves it; its land, labour and trades do not yet cap "
        "that output (Complaints/109).")

FOREIGN_OUTPUT_PER_POPULATION_SHARE = declare(
    "FOREIGN_OUTPUT_PER_POPULATION_SHARE", 1.0, kind="temporary_heuristic",
    unit="a partner's output of a good it can make over the stated national output, per unit of population ratio",
    source=None, confidence="D",
    why="A good bought only as an input has no partner demand figure to size its supply, so a partner that "
        "holds every technique, input and deposit for it makes the stated national output scaled one-for-one "
        "by its population over the one the table is stated for, until an industrial output model sizes it.")


@functools.lru_cache(maxsize=None)
def _final_goods():
    """Goods a household buys for itself (named in data/world/needs.json)."""
    from . import need_data
    return frozenset(need_data.load_needs(ROOT)["goods"])


def budget_scaled_final_tonnes(prices_in_hours, population):
    """{material: tonnes a year} households buy for themselves at these
    prices (labour-hours per unit), scaled down uniformly when the model's
    spending exceeds the income they have. Goods bought as inputs to other
    goods are left out: the model's levels for those are not credible."""
    units = household_demand_by_material(prices_in_hours, population, MEAN_INCOME_HOURS_PER_CAPITA)
    spending = sum(quantity * prices_in_hours.get(material, 0.0)
                   for material, quantity in units.items())
    income = population * MEAN_INCOME_HOURS_PER_CAPITA
    scale = min(1.0, income / spending) if spending > 0.0 else 1.0
    final = _final_goods()
    return {material: quantity * scale * tonnes_per_unit(material)
            for material, quantity in units.items() if material in final}


@functools.lru_cache(maxsize=None)
def household_tonnes_by_material(civilization_id):
    """The economy's households' final-goods demand at its own solved prices."""
    from .foreign_economies import _foreign_prices_in_own_coin
    civilization = load_civ(civilization_id)
    per_hour = starting_schedule(civilization_id).money_per_labour_hour
    prices_in_hours = {material: price / per_hour
                       for material, price in _foreign_prices_in_own_coin(civilization_id).items()
                       if price > 0.0}
    return budget_scaled_final_tonnes(prices_in_hours, float(civilization.get("population") or 0.0))


class ForeignCapacityMixin:

    def home_unmade_demand_tonnes(self, commodity):
        """Tonnes a year this society's own households want of a commodity
        it cannot make, from the same model at its own prices and size now;
        zero when no household good is part of the commodity."""
        prices = self.goods_market.household_prices()
        cache = getattr(self.household, "_home_final_tonnes_cache", None)
        if cache is None or cache[0] is not prices:
            per_hour = self.labour.money_per_labour_hour()
            tonnes = budget_scaled_final_tonnes(
                {material: price / per_hour for material, price in prices.items() if price > 0.0},
                self._opening_population())
            by_commodity = {}
            for material, amount in sorted(tonnes.items()):
                key = self._material_tag(material)[0]
                by_commodity[key] = by_commodity.get(key, 0.0) + amount
            cache = self.household._home_final_tonnes_cache = (prices, by_commodity)
        return cache[1].get(commodity, 0.0) * self.household_demand_ratio(commodity)

    def foreign_supply_tonnes(self, civilization_id, material):
        """Tonnes a year a partner can sell of a material: what its own techniques, inputs and regions
        make, and what it holds. Zero when it cannot make the material. A partner's book, once opened,
        carries its capacity and stock; before that the opening figures stand."""
        facts = self._foreign_economy_facts(civilization_id)
        commodity = self._material_tag(material)[0]
        solved = facts["solved_materials"]
        if material not in solved or not self._foreign_can_make(civilization_id, material, solved):
            return 0.0
        entry = self.state.economy.foreign_market_book.get(civilization_id, {}).get(commodity)
        if entry is not None:
            return entry["capacity_tonnes"] + entry["stock_tonnes"]
        capacity, _demand = self.foreign_opening(civilization_id, commodity, solved)
        if capacity > 0.0 or self._tracked_mineral(commodity):
            return capacity
        # a curated output is the reference empire's; any other is this society's own capacity
        reference = (self.DEFAULT_POPULATION_100AD if commodity in self.res["empire_output_100ad"]
                     else float(self.civ.get("population") or self.DEFAULT_POPULATION_100AD))
        scale = float(load_civ(civilization_id).get("population") or 0.0) / reference
        return self._national_output_tonnes(commodity) * scale * FOREIGN_OUTPUT_PER_POPULATION_SHARE

    def _tracked_mineral(self, commodity):
        """Whether some deposit shares out its output over tiles."""
        return commodity in self.geography.tracked_materials()

    def _foreign_mineral_share(self, civilization_id, commodity):
        """Share of a mined commodity on the tiles it holds."""
        return self.geography.held_share(tiles_held(load_civ(civilization_id), self.world_map), commodity)

    def _foreign_can_make(self, civilization_id, material, solved, _seen=None):
        """Whether its techniques and regions supply the material: it holds
        a technique, every input can be had the same way, and an ore deposit
        on the chain is one its regions hold."""
        cache = self.household.__dict__.setdefault("_foreign_can_make_cache", {})
        key = (civilization_id, material)
        if key in cache:
            return cache[key]
        if material not in solved:
            return False
        seen = _seen or frozenset()
        if material in seen:
            return True
        entry = demand_model.production_data().get(material) or {}
        if "deposit" in str(entry.get("extracted_from") or ""):
            commodity = self._material_tag(material)[0]
            result = (self._tracked_mineral(commodity)
                      and self._foreign_mineral_share(civilization_id, commodity) > 0.0)
        else:
            result = all(self._foreign_can_make(civilization_id, input_material, solved,
                                                seen | {material})
                         for input_material in sorted(entry.get("inputs") or {}))
        if not seen:
            cache[key] = result
        return result

    def _foreign_demand_and_make(self, civilization_id, solved):
        """{commodity: (tonnes wanted, tonnes of that it can make)}."""
        cache = self.household.__dict__.setdefault("_foreign_demand_cache", {})
        cached = cache.get(civilization_id)
        if cached is not None:
            return cached
        by_commodity = {}
        for material, tonnes in sorted(household_tonnes_by_material(civilization_id).items()):
            commodity = self._material_tag(material)[0]
            wanted, made = by_commodity.get(commodity, (0.0, 0.0))
            by_commodity[commodity] = (wanted + tonnes, made + (
                tonnes if self._foreign_can_make(civilization_id, material, solved) else 0.0))
        cache[civilization_id] = by_commodity
        return by_commodity

    def foreign_opening(self, civilization_id, commodity, solved):
        """(capacity tonnes, demand tonnes) a foreign economy opens a
        commodity with. A mined commodity is its regions' share of the
        national output and its own demand; one nothing can make has no
        capacity."""
        wanted, made = self._foreign_demand_and_make(civilization_id, solved).get(
            commodity, (0.0, 0.0))
        if self._tracked_mineral(commodity):
            output = (self._national_output_tonnes(commodity)
                      * self._foreign_mineral_share(civilization_id, commodity))
            return output, (output if output > 0.0 else wanted)
        return made * FOREIGN_OPENING_IN_BALANCE, wanted
