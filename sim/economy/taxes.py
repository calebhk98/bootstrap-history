"""The state's revenue as transfers from those who owe it, never credited from nowhere.

Each form a civilisation declares (`state_revenue` in its data) is assessed per payer on that payer's own
share of the base (taxes_bases.py). In-kind forms move goods from the payers to the state; money forms are
transfers to it. A payer who cannot pay owes arrears; a purse is never overdrawn. Collection is imperfect by
the state's capacity: the share of each liability the state's officials can assess and collect (the engine
reads the same 0..1 field as how far the state's writ runs). What is not collected is evaded, not owed.
"""
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from .taxes_bases import Base, YearFacts, measure
from .types import AgentId, GoodId, GoodsMove, TileId, Transfer, is_edge

__all__ = ["TaxForm", "Arrear", "Assessment", "YearFacts", "forms_from_civ_data", "assess"]


@dataclass(frozen=True)
class TaxForm:
    name: str
    basis: str
    rate: float
    paid_in: str = ""                # a good: the form is taken in kind; empty: paid in money
    tiles: Optional[FrozenSet[TileId]] = None   # the tiles a form on the harvest is levied on; None: all
    except_tiles: FrozenSet[TileId] = frozenset()   # tiles it is not levied on

    def covers(self, tile: TileId) -> bool:
        return (self.tiles is None or tile in self.tiles) and tile not in self.except_tiles


@dataclass(frozen=True)
class Arrear:
    payer: AgentId
    form: str
    amount: float                    # money owed, or quantity of `good` when taken in kind
    good: GoodId = ""


@dataclass(frozen=True)
class Assessment:
    form: str
    basis: str
    base_value: float                # money's worth of the whole base
    due_value: float                 # money's worth the state's officials could assess
    collected_value: float           # money's worth that reached the state (goods at the year's price)
    evaded_value: float              # money's worth the state could not assess
    collected_quantity: float        # goods collected in kind; zero for a money form
    arrears: Tuple[Arrear, ...]


# Bases the actor layer assesses on the purses of the actors it names (sim/agents/revenue_bases.py), not the economy.
ACTOR_LAYER_BASES = frozenset({"stratum_income", "land_rent", "land_value"})


def forms_from_civ_data(state_revenue: Sequence[Mapping]) -> Tuple[TaxForm, ...]:
    """The forms the economy assesses; a form on a base only the actor layer measures is left to it."""
    return tuple(TaxForm(str(entry["form"]), str(entry["basis"]), float(entry["rate"]), str(entry.get("paid_in") or ""),
                         None if entry.get("tiles") is None else frozenset(entry["tiles"]),
                         frozenset(entry.get("except_tiles") or ()))
                 for entry in state_revenue if entry["basis"] not in ACTOR_LAYER_BASES)


def assess(forms: Sequence[TaxForm], facts: YearFacts, state_agent_id: AgentId, prices: Mapping[GoodId, float],
           state_capacity: float = 1.0) -> Tuple[List[Transfer], List[GoodsMove], List[Assessment]]:
    if not 0.0 <= state_capacity <= 1.0:
        raise ValueError("state_capacity must lie in 0..1, got %r" % state_capacity)
    cash_left: Dict[AgentId, float] = dict(facts.cash)
    held_left: Dict[Tuple[AgentId, GoodId], float] = {}
    transfers: List[Transfer] = []
    moves: List[GoodsMove] = []
    assessments: List[Assessment] = []
    for form in forms:
        bases = measure(form.basis, form, facts, prices)
        if form.paid_in:
            assessments.append(_collect_in_kind(form, bases, facts, state_agent_id, prices, state_capacity,
                                                held_left, moves))
        else:
            assessments.append(_collect_money(form, bases, facts, state_agent_id, state_capacity, cash_left,
                                              transfers))
    return transfers, moves, assessments


def _collect_money(form, bases: Mapping[AgentId, Base], facts: YearFacts, state_agent_id, state_capacity,
                   cash_left: Dict[AgentId, float], transfers: List[Transfer]) -> Assessment:
    base_total = due_total = collected_total = 0.0
    arrears = []
    for payer, base in sorted(bases.items()):
        if payer == state_agent_id:
            continue
        due = form.rate * base.value * state_capacity
        available = 0.0 if is_edge(payer) else max(0.0, cash_left.get(payer, 0.0))
        paid = min(due, available)
        if paid > 0.0:
            transfers.append(Transfer(payer, state_agent_id, facts.currency, paid, "tax:" + form.name))
            cash_left[payer] = available - paid
        if due - paid > 0.0:
            arrears.append(Arrear(payer, form.name, due - paid))
        base_total += base.value
        due_total += due
        collected_total += paid
    return Assessment(form.name, form.basis, base_total, due_total, collected_total,
                      form.rate * base_total * (1.0 - state_capacity), 0.0, tuple(arrears))


def _collect_in_kind(form, bases: Mapping[AgentId, Base], facts: YearFacts, state_agent_id, prices, state_capacity,
                     held_left: Dict[Tuple[AgentId, GoodId], float], moves: List[GoodsMove]) -> Assessment:
    price = prices.get(form.paid_in, 0.0)
    base_total = due_total = collected_quantity = 0.0
    arrears = []
    for payer, base in sorted(bases.items()):
        if payer == state_agent_id:
            continue
        due = form.rate * base.quantity * state_capacity
        key = (payer, base.good)
        if key not in held_left:
            held_left[key] = base.quantity if facts.held_goods is None else facts.held_goods.get(key, 0.0)
        paid = min(due, max(0.0, held_left[key]))
        if paid > 0.0:
            moves.append(GoodsMove(payer, state_agent_id, base.good, base.tile, paid, "tax:" + form.name))
            held_left[key] -= paid
        if due - paid > 0.0:
            arrears.append(Arrear(payer, form.name, due - paid, base.good))
        base_total += base.value
        due_total += due * price
        collected_quantity += paid
    return Assessment(form.name, form.basis, base_total, due_total, collected_quantity * price,
                      form.rate * base_total * (1.0 - state_capacity), collected_quantity, tuple(arrears))
