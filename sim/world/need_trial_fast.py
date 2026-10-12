"""`SingleMaterialTrial.weighted_final` without the per-call object building.

Everything that does not depend on the trial price is laid out once: which needs are priced, the
constant needs' price indexes and spending shares, the repriced needs' goods and effectiveness. A call
then does the same arithmetic, operation for operation and in the same order, as the general path in
`need_final_demand` (`priced_need`, `_units_per_need`, the spending loop), so the answers are identical
to it bit for bit.
"""
import math
from typing import List, Optional, Tuple

from sim.world import demand
from sim.world.need_basket import NeedSpec


class _Repriced:
    """One need that lists the trial material: its goods other than the material are fixed."""

    def __init__(self, position: int, spec, exponent: float, base_get, material: str):
        self.position = position
        self.effects: List[float] = []
        self.prices: List[float] = []
        self.weights: List[float] = []
        self.material_slot = -1
        for good, effect in spec.goods:
            if good == material:
                if not effect > 0.0:
                    continue
                self.material_slot = len(self.effects)
                self.prices.append(1.0)
                self.weights.append(0.0)
                self.effects.append(effect)
                continue
            price = base_get(good)
            if price is not None and price > 0.0 and effect > 0.0:
                self.prices.append(price)
                self.weights.append((price / effect) ** exponent)
                self.effects.append(effect)
        self.exponent = exponent
        self.slots: Tuple[int, ...] = ()

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


class FastWeighted:
    """Built from a `SingleMaterialTrial` (and its `_TrialLayout` of a reference pricing)."""

    def __init__(self, trial, layout, priced_reference):
        model = trial.model
        self.model = model
        self.layout = layout
        self.bins = [(income_bin.income_per_capita_per_year, income_bin.population)
                     for income_bin in model.bins]
        goods = layout.goods
        self.subsistence = [good.subsistence_quantity_per_capita_per_year for good in goods]
        self.marginal = [good.marginal_budget_share for good in goods]
        self.budget_weights = [need.spec.budget_weight for need in priced_reference]
        self.weight_total = layout.budget_weight_total
        self.indexes = layout.indexes
        self.count = len(goods)
        self.price_indexes = [need.price_index for need in priced_reference]
        self.rows: List[List[Tuple[int, float, float]]] = [
            [(slot, good[1], good[3]) for slot, good in zip(slots, need.goods)]
            for slots, need in zip(self.indexes, priced_reference)]
        # the priced positions that list the material, in the order of the priced list
        self.repriced: List[_Repriced] = []
        position = 0
        base_get = trial.prices.get
        for slot in trial._slots:
            if isinstance(slot, NeedSpec):
                candidate = _Repriced(position, slot, trial._exponent, base_get, trial.material)
                if candidate.material_slot >= 0:
                    candidate.slots = self.indexes[position]
                    self.repriced.append(candidate)
                if candidate.effects:
                    position += 1
            elif slot is not None:
                position += 1
        self.own_index = layout.order.get(trial.material)
        self.weights = layout.weights

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
