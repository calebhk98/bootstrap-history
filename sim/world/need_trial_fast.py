"""`SingleMaterialTrial.weighted_final` without the per-call object building.

Everything that does not depend on the trial price is laid out once: which needs are priced, the
constant needs' price indexes and spending shares, the repriced needs' goods and effectiveness. A call
then does the same arithmetic, operation for operation and in the same order, as the general path in
`need_final_demand` (`priced_need`, `_units_per_need`, the spending loop), so the answers are identical
to it bit for bit.
"""
import math
from typing import Dict, List, Tuple

from sim.world import demand


class _Repriced:
    """One need that lists the trial material: its goods other than the material are fixed."""

    def __init__(self, position: int, spec, exponent: float, base_get, material: str):
        self.position = position
        self.names: List[str] = []
        self.effects: List[float] = []
        self.prices: List[float] = []
        self.weights: List[float] = []
        self.material_slot = -1
        for good, effect in spec.goods:
            if good == material:
                if not effect > 0.0:
                    continue
                self.material_slot = len(self.effects)
                self.names.append(good)
                self.prices.append(1.0)
                self.weights.append(0.0)
                self.effects.append(effect)
                continue
            price = base_get(good)
            if price is not None and price > 0.0 and effect > 0.0:
                self.names.append(good)
                self.prices.append(price)
                self.weights.append((price / effect) ** exponent)
                self.effects.append(effect)
        self.exponent = exponent
        self.slots: Tuple[int, ...] = ()

    def price_without_material(self) -> Tuple[float, List[float]]:
        """(price index, shares) of a need whose listing of the material gives it no effect."""
        power = math.fsum(self.weights)
        shares = [weight / power for weight in self.weights]
        units_per_money = math.fsum([share * effect / price for share, effect, price
                                     in zip(shares, self.effects, self.prices)])
        return 1.0 / units_per_money, shares

    def price(self, material_price: float) -> Tuple[float, List[float]]:
        """(price index, spending shares in goods order) with the material at `material_price`."""
        slot = self.material_slot
        prices = self.prices
        weights = self.weights
        effects = self.effects
        prices[slot] = material_price
        weights[slot] = (material_price / effects[slot]) ** self.exponent
        power = math.fsum(weights)
        shares = [weight / power for weight in weights]
        units_per_money = math.fsum([share * effect / price for share, effect, price
                                     in zip(shares, effects, prices)])
        return 1.0 / units_per_money, shares


def _constant_need(spec, exponent: float, base_get):
    """(goods, prices, price index, spending shares) of a need that does not list the trial material,
    as `need_basket.priced_need` computes them; None when no good of it has a price."""
    goods: List[str] = []
    effects: List[float] = []
    prices: List[float] = []
    weights: List[float] = []
    for good, effect in spec.goods:
        price = base_get(good)
        if price is not None and price > 0.0 and effect > 0.0:
            goods.append(good)
            effects.append(effect)
            prices.append(price)
            weights.append((price / effect) ** exponent)
    if not goods:
        return None
    power = math.fsum(weights)
    shares = [weight / power for weight in weights]
    units_per_money = math.fsum([share * effect / price for share, effect, price in zip(shares, effects, prices)])
    return goods, prices, 1.0 / units_per_money, shares


class FastWeighted:
    """Built from a `SingleMaterialTrial`: lays out the priced needs the way `_TrialLayout` and
    `_Layout` do (the needs that have a priced good, the materials in the order demand first meets them,
    budget shares among the priced needs)."""

    def __init__(self, trial):
        model = trial.model
        exponent = trial._exponent
        base_get = trial.prices.get
        material = trial.material
        specs = []
        names: List[List[str]] = []
        self.price_indexes: List[float] = []
        self.rows: List[List[Tuple[int, float, float]]] = []
        pending = []                       # (position, rows builder input) for the later slot numbers
        self.repriced: List[_Repriced] = []
        for spec in model.basket.needs:
            if any(good == material for good, _effect in spec.goods):
                candidate = _Repriced(len(specs), spec, exponent, base_get, material)
                if not candidate.effects:
                    continue
                if candidate.material_slot >= 0:
                    self.repriced.append(candidate)
                goods = candidate.names
                prices, price_index, shares = candidate.prices, 1.0, [0.0] * len(goods)
                if candidate.material_slot < 0:
                    price_index, shares = candidate.price_without_material()
            else:
                found = _constant_need(spec, exponent, base_get)
                if found is None:
                    continue
                goods, prices, price_index, shares = found
            specs.append(spec)
            names.append(goods)
            self.price_indexes.append(price_index)
            pending.append((prices, shares))
        self.count = len(specs)
        order: Dict[str, int] = {}
        indexes = tuple(tuple(order.setdefault(good, len(order)) for good in goods) for goods in names)
        for repriced in self.repriced:
            repriced.slots = indexes[repriced.position]
        self.rows = [list(zip(slots, prices, shares)) for slots, (prices, shares) in zip(indexes, pending)]
        self.ok = self.count > 0
        weight_total = sum(spec.budget_weight for spec in specs)
        self.subsistence = [spec.subsistence_per_person for spec in specs]
        self.budget_weights = [spec.budget_weight for spec in specs]
        self.marginal = [spec.budget_weight / weight_total for spec in specs]
        self.weight_total = math.fsum(spec.budget_weight for spec in specs)
        self.bins = [(income_bin.income_per_capita_per_year, income_bin.population)
                     for income_bin in model.bins]
        self.own_index = order.get(material)
        self.weights = [trial._weight_of_material.get(good, 0.0) for good in order]

    def __call__(self, material_price: float):
        price_indexes = self.price_indexes
        rows = self.rows
        for repriced in self.repriced:
            position = repriced.position
            price_indexes[position], shares = repriced.price(material_price)
            rows[position] = list(zip(repriced.slots, repriced.prices, shares))
        subsistence = self.subsistence
        floor_costs = [price_index * floor for price_index, floor in zip(price_indexes, subsistence)]
        committed = math.fsum(floor_costs)
        covered_population = 0.0
        covered_surplus = 0.0
        units = None
        for income, population in self.bins:
            surplus = income - committed
            if surplus >= 0.0:
                covered_population += population
                covered_surplus += population * surplus
                continue
            if units is None:
                units = [0.0] * self.count
                committed_per_capita = sum(floor_costs)
            floor_scale, flexible_spending = demand.household_spending_split(income, committed_per_capita)
            for index, marginal in enumerate(self.marginal):
                units[index] += population * (subsistence[index] * floor_scale
                                              + (marginal / price_indexes[index]) * flexible_spending)
        weight_total = self.weight_total
        if covered_surplus > 0.0 and weight_total > 0.0:
            totals = [floor * covered_population + covered_surplus * budget_weight / weight_total / price_index
                      for floor, budget_weight, price_index in zip(subsistence, self.budget_weights, price_indexes)]
        else:
            totals = [floor * covered_population for floor in subsistence]
        if units is not None:
            totals = [below + covered for below, covered in zip(units, totals)]
        quantity = [0.0] * len(self.weights)
        for price_index, total, need_rows in zip(price_indexes, totals, rows):
            spending = price_index * total
            for slot, good_price, share in need_rows:
                quantity[slot] += spending * share / good_price
        own = self.own_index
        return (0.0 if own is None else quantity[own]), sum(
            [weight * amount for weight, amount in zip(self.weights, quantity)])
