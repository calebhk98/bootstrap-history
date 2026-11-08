"""Cash each employer's year plan assigns to no line (Complaint 644): the room it has for a capital outlay such as
buying bonded people (labour/market/bonded_room.py). A plan has lines (wages, goods or inputs, cash held back);
what is left of the cash after them is free. Every employer is read the same way."""
from typing import Dict, Iterable, Mapping

from .state_budget import StateBudget


def free_cash(cash: float, lines: Iterable[float]) -> float:
    """Cash left after the plan's lines; never below zero."""
    return max(0.0, cash - sum(max(0.0, line) for line in lines))


def by_employer(plans: Mapping[str, object], state_agent: str, budget: StateBudget, balance_of) -> Dict[str, float]:
    """Free cash of each producer (its plan's wage line and input bids) and of the state (its wage and goods
    budgets and the cash it holds back), by employer id. `balance_of(employer)` is the cash held."""
    room = {producer_id: free_cash(balance_of(producer_id), [plan.wage_line] + [bid.budget for bid in plan.bids])
            for producer_id, plan in sorted(plans.items())}
    room[state_agent] = free_cash(balance_of(state_agent), [budget.wage_budget, budget.goods_budget, budget.held_back])
    return {employer: amount for employer, amount in room.items() if amount > 0.0}


def by_plan_table(plans, state_agent: str, budget: StateBudget, balance_of, cash) -> Dict[str, float]:
    """`by_employer` over a `PlanTable`: `cash` is each producer's money in the table's order (one block read of the book), the plan's
    lines are the table's `outlay_total` column (the wage line and the input budgets, added as `by_employer` adds them)."""
    room = (cash - plans.outlay_total).tolist()
    found = {producer_id: amount for producer_id, amount in zip(plans.ids, room) if amount > 0.0}
    state_room = free_cash(balance_of(state_agent), [budget.wage_budget, budget.goods_budget, budget.held_back])
    if state_room > 0.0:
        found[state_agent] = state_room
    return found
