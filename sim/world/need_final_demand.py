"""Household final demand from priced needs.

`quantities_from_priced` is the whole of `NeedDemandModel.final_demand` once the needs are priced.
"""
import collections
import math
from typing import Dict, Optional, Sequence

from sim.world import demand, need_basket
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
