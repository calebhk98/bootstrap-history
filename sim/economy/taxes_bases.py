"""What a state's revenue forms are assessed on, measured per payer from one year's facts.

A basis is a function (form, facts, prices) -> {payer: Base}; the registry maps each basis name a civilisation's
data uses to its function. Adding a basis is one function and one registry line; no civilisation, form or
good id appears here. The names match the bases the engine's `sim/engine/actors/revenue_bases.py` reads.
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping, Optional, Tuple

from .types import AgentId, CurrencyId, GoodId, TileId, is_edge


@dataclass(frozen=True)
class YearFacts:
    """One year's physical and monetary record the bases measure. Plain data, built by the year loop."""
    currency: CurrencyId
    output: Mapping[Tuple[AgentId, GoodId], float] = field(default_factory=dict)     # grown or made by (producer, good)
    producer_tile: Mapping[AgentId, TileId] = field(default_factory=dict)            # where a producer's output lies
    working_people: Mapping[AgentId, float] = field(default_factory=dict)            # by household cohort, soldiers under arms excluded
    wage_per_labour_year: Mapping[AgentId, float] = field(default_factory=dict)      # by cohort: money for one working person-year
    imports_paid: Mapping[Tuple[AgentId, GoodId], float] = field(default_factory=dict)    # money paid to EDGE_EXTERNAL
    exports_received: Mapping[Tuple[AgentId, GoodId], float] = field(default_factory=dict)  # money received from EDGE_EXTERNAL
    cash: Mapping[AgentId, float] = field(default_factory=dict)                      # money held at the year's close
    sales: Mapping[Tuple[AgentId, GoodId], float] = field(default_factory=dict)      # money received by (seller, good)
    held_goods: Optional[Mapping[Tuple[AgentId, GoodId], float]] = None              # stock held; None: output is assumed held


@dataclass(frozen=True)
class Base:
    value: float                     # money's worth of the base
    quantity: float = 0.0            # physical amount where the base is a good, so a share can be paid in kind
    good: GoodId = ""
    tile: TileId = ""


def _sum_by_agent(pairs: Mapping[Tuple[AgentId, GoodId], float]) -> Dict[AgentId, float]:
    totals: Dict[AgentId, float] = {}
    for (agent, _good), amount in sorted(pairs.items()):
        totals[agent] = totals.get(agent, 0.0) + amount
    return totals


def harvest(form, facts: YearFacts, prices: Mapping[GoodId, float]) -> Dict[AgentId, Base]:
    """Each grower's output of the good the form is paid in: a share of what was grown is taken in kind."""
    if not form.paid_in:
        raise ValueError("form %r on basis 'harvest' must name the good it is paid in (paid_in)" % form.name)
    price = prices.get(form.paid_in, 0.0)
    bases = {}
    for (producer, good), quantity in sorted(facts.output.items()):
        if good == form.paid_in and quantity > 0.0:
            bases[producer] = Base(quantity * price, quantity, good, facts.producer_tile.get(producer, ""))
    return bases


def adult_labour_years(form, facts: YearFacts, prices: Mapping[GoodId, float]) -> Dict[AgentId, Base]:
    """Each cohort's working people, each worth a year of labour at the cohort's wage."""
    return {cohort: Base(people * facts.wage_per_labour_year.get(cohort, 0.0))
            for cohort, people in sorted(facts.working_people.items()) if people > 0.0}


def imports_value(form, facts: YearFacts, prices: Mapping[GoodId, float]) -> Dict[AgentId, Base]:
    return {agent: Base(total) for agent, total in _sum_by_agent(facts.imports_paid).items() if total > 0.0}


def exports_value(form, facts: YearFacts, prices: Mapping[GoodId, float]) -> Dict[AgentId, Base]:
    return {agent: Base(total) for agent, total in _sum_by_agent(facts.exports_received).items() if total > 0.0}


def sales_value(form, facts: YearFacts, prices: Mapping[GoodId, float]) -> Dict[AgentId, Base]:
    return {agent: Base(total) for agent, total in _sum_by_agent(facts.sales).items() if total > 0.0}


def coin_stock(form, facts: YearFacts, prices: Mapping[GoodId, float]) -> Dict[AgentId, Base]:
    """Money held by each agent: the wealth the economy models as a stock. Edge accounts hold none that is taxable."""
    return {agent: Base(amount) for agent, amount in sorted(facts.cash.items())
            if amount > 0.0 and not is_edge(agent)}


BASES: Dict[str, Callable] = {
    "harvest": harvest,
    "adult_labour_years": adult_labour_years,
    "imports_value": imports_value,
    "exports_value": exports_value,
    "sales_value": sales_value,
    "coin_stock": coin_stock,
}


def measure(basis: str, form, facts: YearFacts, prices: Mapping[GoodId, float]) -> Dict[AgentId, Base]:
    function = BASES.get(basis)
    if function is None:
        raise ValueError("unknown tax basis %r (form %r); known bases: %s"
                         % (basis, form.name, ", ".join(sorted(BASES))))
    return function(form, facts, prices)
