"""Household final demand from priced needs, and the same demand re-evaluated while one price moves.

`quantities_from_priced` is the whole of `NeedDemandModel.final_demand` once the needs are priced.
`SingleMaterialTrial` answers "what would final demand be if only this material's price changed?" many
times over: every need that does not sell the material keeps the priced result of the base prices, so a
trial reprices only the needs that do. The arithmetic is the same operations on the same values as a
full evaluation, so the answers are identical to it.
"""
import collections
from typing import Dict, List, Mapping, Optional, Sequence

from sim.world import demand, need_basket
from sim.world.need_basket import PricedNeed


def quantities_from_priced(model, priced: Sequence[PricedNeed]) -> Dict[str, float]:
    """{material: units households want per year} for needs priced at some prices: floors, price index and
    the surplus split from the need-basket kernel; below the committed cost of every floor the
    protected-floor rule of sim/world/demand.py applies per income bin."""
    if not priced:
        return {}
    weight_total = sum(need.spec.budget_weight for need in priced)
    price_index = {need.spec.need_id: need.price_index for need in priced}
    goods = tuple(demand.Good(need.spec.need_id, need.spec.subsistence_per_person,
                              need.spec.budget_weight / weight_total) for need in priced)
    need_units = {need.spec.need_id: 0.0 for need in priced}
    committed = need_basket.subsistence_cost_per_person(priced)
    # what a household's floors cost, as the per-person demand formula sums it
    committed_per_capita = sum(price_index[good.name] * good.subsistence_quantity_per_capita_per_year
                               for good in goods)
    covered_population = 0.0
    covered_surplus = 0.0
    for income_bin in model.bins:
        surplus = income_bin.income_per_capita_per_year - committed
        if surplus >= 0.0:
            covered_population += income_bin.population
            covered_surplus += income_bin.population * surplus
            continue
        income = income_bin.income_per_capita_per_year
        for good in goods:
            need_units[good.name] += (
                income_bin.population * demand.household_quantity_demanded_given_committed(
                    good, price_index[good.name], income, committed_per_capita))
    _floors, covered_units = need_basket.need_units(
        priced, model.basket, covered_population, covered_surplus, satiate=False)
    for need_id, units in covered_units.items():
        need_units[need_id] += units
    if model.satiate:
        need_basket.limit_satiation(need_units, priced, model.basket,
                                    sum(income_bin.population for income_bin in model.bins))
    quantities: Dict[str, float] = collections.defaultdict(float)
    for need in priced:
        spending = need.price_index * need_units[need.spec.need_id]
        for material, price, _effect, share in need.goods:
            quantities[material] += spending * share / price
    return dict(quantities)


class SingleMaterialTrial:
    """Final demand at `prices` with one material's price replaced, repeatedly.

    Needs that do not list the material are priced once from `prices`; each call to `final_demand` reprices
    only those that do. `prices` must not change while the trial is in use."""

    def __init__(self, model, prices: Mapping[str, float], material: str):
        self.model = model
        self.material = material
        self.prices = prices
        exponent = 1.0 - model.basket.substitution
        self._exponent = exponent
        self._slots: List = []        # per basket need: a PricedNeed, None (unpriced), or the spec to reprice
        for spec in model.basket.needs:
            if any(good == material for good, _effect in spec.goods):
                self._slots.append(spec)
            else:
                self._slots.append(need_basket.priced_need(spec, exponent, prices.get))

    def final_demand(self, price: float) -> Dict[str, float]:
        """Final demand with the material at `price`."""
        material = self.material
        base_get = self.prices.get

        def price_of(good: str) -> Optional[float]:
            return price if good == material else base_get(good)

        priced = []
        for slot in self._slots:
            if isinstance(slot, need_basket.NeedSpec):
                slot = need_basket.priced_need(slot, self._exponent, price_of)
            if slot is not None:
                priced.append(slot)
        return quantities_from_priced(self.model, priced)
