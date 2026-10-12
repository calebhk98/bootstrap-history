"""Household final demand from priced needs, and the same demand re-evaluated while one price moves.

`quantities_from_priced` is the whole of `NeedDemandModel.final_demand` once the needs are priced.
`SingleMaterialTrial` answers "what would final demand be if only this material's price changed?" many
times over: every need that does not sell the material keeps the priced result of the base prices, so a
trial reprices only the needs that do. The arithmetic is the same operations on the same values as a
full evaluation, so the answers are identical to it.
"""
import collections
import math
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from sim.world import demand, need_basket, need_trial_fast
from sim.world.need_basket import PricedNeed


class _Layout:
    """What final demand reads from a priced list that does not depend on the prices: which needs are
    priced, how many goods each lists, their floors and their budget shares."""

    def __init__(self, priced: Sequence[PricedNeed]):
        self.specs = tuple(need.spec for need in priced)
        weight_total = sum(need.spec.budget_weight for need in priced)
        self.goods = tuple(demand.Good(need.spec.need_id, need.spec.subsistence_per_person,
                                       need.spec.budget_weight / weight_total) for need in priced)
        self.budget_weight_total = math.fsum(need.spec.budget_weight for need in priced)


def _units_per_need(model, priced: Sequence[PricedNeed], layout: Optional[_Layout]) -> Dict[str, float]:
    """{need id: units households want per year}: the below-floor bins' protected purchases, then the
    covered bins' floors and surplus split."""
    layout = layout or _Layout(priced)
    goods = layout.goods
    price_indexes = [need.price_index for need in priced]
    floor_costs = [price_index * good.subsistence_quantity_per_capita_per_year
                   for price_index, good in zip(price_indexes, goods)]
    committed = math.fsum(floor_costs)
    # what a household's floors cost, as the per-person demand formula sums it
    committed_per_capita = sum(floor_costs)
    units = [0.0] * len(goods)
    covered_population = 0.0
    covered_surplus = 0.0
    for income_bin in model.bins:
        surplus = income_bin.income_per_capita_per_year - committed
        if surplus >= 0.0:
            covered_population += income_bin.population
            covered_surplus += income_bin.population * surplus
            continue
        floor_scale, flexible_spending = demand.household_spending_split(
            income_bin.income_per_capita_per_year, committed_per_capita)
        population = income_bin.population
        for index, good in enumerate(goods):
            units[index] += population * (
                good.subsistence_quantity_per_capita_per_year * floor_scale
                + (good.marginal_budget_share / price_indexes[index]) * flexible_spending)
    need_units = {good.name: total for good, total in zip(goods, units)}
    _floors, covered_units = need_basket.need_units(
        priced, model.basket, covered_population, covered_surplus, satiate=False,
        weight_total=layout.budget_weight_total)
    for need_id, covered in covered_units.items():
        need_units[need_id] += covered
    if model.satiate:
        need_basket.limit_satiation(need_units, priced, model.basket,
                                    sum(income_bin.population for income_bin in model.bins))
    return need_units


def quantities_from_priced(model, priced: Sequence[PricedNeed],
                           layout: Optional[_Layout] = None) -> Dict[str, float]:
    """{material: units households want per year} for needs priced at some prices: floors, price index and
    the surplus split from the need-basket kernel; below the committed cost of every floor the
    protected-floor rule of sim/world/demand.py applies per income bin. `layout` is the `_Layout` of
    this very priced list, when the caller holds one."""
    if not priced:
        return {}
    need_units = _units_per_need(model, priced, layout)
    quantities: Dict[str, float] = collections.defaultdict(float)
    for need in priced:
        spending = need.price_index * need_units[need.spec.need_id]
        for material, price, _effect, share in need.goods:
            quantities[material] += spending * share / price
    return dict(quantities)


class _TrialLayout(_Layout):
    """A `_Layout` that also numbers the materials in the order final demand first meets them."""

    def __init__(self, priced: Sequence[PricedNeed], weight_of_material: Mapping[str, float]):
        super().__init__(priced)
        order: Dict[str, int] = {}
        self.indexes = tuple(tuple(order.setdefault(good[0], len(order)) for good in need.goods)
                             for need in priced)
        self.order = order
        self.weights = [weight_of_material.get(material, 0.0) for material in order]


class SingleMaterialTrial:
    """Final demand at `prices` with one material's price replaced, repeatedly.

    Needs that do not list the material are priced once from `prices`; each call reprices only those that
    do. `prices` must not change while the trial is in use. The material's price is positive in every
    trial, so which needs are priced, and which goods each lists, is the same in every call."""

    def __init__(self, model, prices: Mapping[str, float], material: str,
                 weight_of_material: Optional[Mapping[str, float]] = None):
        self.model = model
        self.material = material
        self.prices = prices
        self._weight_of_material = weight_of_material or {}
        self._exponent = 1.0 - model.basket.substitution
        self._layouts: Dict[Tuple[bool, ...], _TrialLayout] = {}
        self._fast = None             # built on the first weighted_final call
        self._slots: List = []        # per basket need: a PricedNeed, None (unpriced), or the spec to reprice
        for spec in model.basket.needs:
            if any(good == material for good, _effect in spec.goods):
                self._slots.append(spec)
            else:
                self._slots.append(need_basket.priced_need(spec, self._exponent, prices.get, False))

    def _priced(self, price: float):
        """(the priced needs, which of the repriced needs are priced)."""
        material = self.material
        base_get = self.prices.get

        def price_of(good: str) -> Optional[float]:
            return price if good == material else base_get(good)

        priced = []
        present = []
        for slot in self._slots:
            if isinstance(slot, need_basket.NeedSpec):
                slot = need_basket.priced_need(slot, self._exponent, price_of, False)
                present.append(slot is not None)
            if slot is not None:
                priced.append(slot)
        return priced, tuple(present)

    def _build_fast(self):
        """The precomputed evaluator of `need_trial_fast`, or False where the general path must be used."""
        if self.model.satiate:
            return False
        priced, present = self._priced(1.0)
        if not priced:
            return False
        layout = self._layouts.get(present)
        if layout is None:
            layout = self._layouts[present] = _TrialLayout(priced, self._weight_of_material)
        return need_trial_fast.FastWeighted(self, layout, priced)

    def final_demand(self, price: float) -> Dict[str, float]:
        """Final demand with the material at `price`."""
        return quantities_from_priced(self.model, self._priced(price)[0])

    def weighted_final(self, price: float):
        """(units of the material households want, sum over materials of weight times units households want)
        with the material at `price`, summed in the order `final_demand` lists the materials. The weights
        are those given at construction."""
        if self._fast is None:
            self._fast = self._build_fast()
        if self._fast and price > 0.0:
            return self._fast(price)
        priced, present = self._priced(price)
        if not priced:
            return 0.0, 0
        layout = self._layouts.get(present)
        if layout is None:
            layout = self._layouts[present] = _TrialLayout(priced, self._weight_of_material)
        need_units = _units_per_need(self.model, priced, layout)
        quantity = [0.0] * len(layout.order)
        for need, indexes in zip(priced, layout.indexes):
            spending = need.price_index * need_units[need.spec.need_id]
            for index, (_material, good_price, _effect, share) in zip(indexes, need.goods):
                quantity[index] += spending * share / good_price
        own = layout.order.get(self.material)
        return (0.0 if own is None else quantity[own]), sum(
            [weight * units for weight, units in zip(layout.weights, quantity)])
