"""The state as a buyer: each year it spends its revenue and part of any cash above its reserve, bidding
for hours in the labour market and for goods in the goods markets like anyone else, and covers a
shortfall by the policy's order (state_finance.py). Goods already in its stores are used before it buys."""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from sim.constants import declare

from . import households_basket, state_finance
from .setup import labour_area
from .types import Bid, EDGE_CONSUMPTION, GoodsMove, LabourBid

STATE_MAX_SHARE_OF_TILE_HOURS = declare(
    "STATE_MAX_SHARE_OF_TILE_HOURS", 0.3, kind="temporary_heuristic",
    unit="share of a tile's working hours the state will bid for",
    source=None, confidence="D",
    why="Stands in for the size of the state's establishment (how many soldiers and officials it can "
        "house, drill and supervise), which the engine does not yet supply.")
STATE_WAGE_CEILING_MULTIPLE = declare(
    "STATE_WAGE_CEILING_MULTIPLE", 1.5, kind="temporary_heuristic",
    unit="multiple of last year's wage the state will bid",
    source=None, confidence="D",
    why="How far above last year's wage the state is willing to go to fill its posts; the labour market "
        "moves the wage only part of the way anyway.")


@dataclass
class StateBudget:
    revenue: float = 0.0                 # money the state took in last year (taxes and sales)
    wage_budget: float = 0.0             # this year's plan
    goods_budget: float = 0.0
    deficit: float = 0.0
    financed: Dict[str, float] = field(default_factory=dict)   # what each method supplied this year
    issued_total: float = 0.0


def plan_year(setup, record, view, labour_bids: List[LabourBid]) -> None:
    """Fix this year's spending and its financing, and add the state's bids for hours to `labour_bids`."""
    policy, budget = setup.state_policy, record.state_budget
    money, state = setup.currency_id, setup.state_agent
    cash = record.book.balance(state, money)
    reserve = policy.reserve_years_of_revenue * budget.revenue
    spendable = min(cash, budget.revenue + policy.cash_spend_share * max(0.0, cash - budget.revenue - reserve))
    planned = spendable
    if policy.real_spending_target > 0.0:
        # a stated programme is paid from every coin on hand first, then financed
        planned = policy.real_spending_target * view.basket_price_level(money)
        spendable = min(cash, planned)
    deficit = max(0.0, planned - spendable)
    in_hand, expected, supplied = state_finance.finance_deficit(policy, record, view, setup, deficit, budget.revenue)
    planned = min(planned, spendable + in_hand + expected)
    now = spendable + in_hand
    budget.wage_budget = min(policy.wage_share * planned, now)
    budget.goods_budget = planned - budget.wage_budget
    budget.deficit = deficit
    budget.financed = supplied
    budget.issued_total += supplied.get("issue", 0.0) + supplied.get("debase", 0.0)
    labour_bids.extend(_labour_bids(setup, record, view, budget.wage_budget))


def _trades(setup):
    trades = [trade for trade in setup.state_policy.trades if trade in setup.trades]
    return trades or [setup.unskilled_trade]


def _labour_bids(setup, record, view, wage_budget: float) -> List[LabourBid]:
    if wage_budget <= 0.0:
        return []
    working: Dict[str, float] = {}
    for cohort in record.cohorts.values():
        working[cohort.tile] = working.get(cohort.tile, 0.0) + cohort.working_people
    total_working = math.fsum(working.values())
    if total_working <= 0.0:
        return []
    trades = _trades(setup)
    level = view.basket_price_level(setup.currency_id)
    bids = []
    for trade in trades:
        for tile, people in sorted(working.items()):
            area = labour_area(tile)
            wage = view.wage(trade, area) or setup.opening_wages.get(trade, 0.0) * level
            if wage <= 0.0:
                continue
            ceiling = wage * STATE_WAGE_CEILING_MULTIPLE
            hours = min(wage_budget / len(trades) * people / total_working / ceiling,
                        people * setup.working_hours_per_year * STATE_MAX_SHARE_OF_TILE_HOURS)
            if hours > 0.0:
                bids.append(LabourBid(setup.state_agent, trade, area, hours, ceiling))
    return bids


def goods_bids(setup, record, view, area_map, order_book) -> None:
    """Spend the goods budget across the basket's needs by their weights and each need's goods by the
    household mix; stores already held are used up first and cost nothing."""
    budget = record.state_budget
    if budget.goods_budget <= 0.0:
        return
    tile = setup.capital_tile
    basket = setup.basket_for(tile)
    priced = households_basket.need_prices(basket, view, tile)
    weight_total = math.fsum(need.spec.budget_weight for need in priced)
    if weight_total <= 0.0:
        return
    state = setup.state_agent
    moves = []
    for need in priced:
        need_budget = budget.goods_budget * need.spec.budget_weight / weight_total
        for good, price, _effect, share in need.goods:
            wanted = need_budget * share / price
            held = [(held_tile, quantity) for held_tile, quantity in
                    sorted(record.book.holdings(state)["goods"].get(good, {}).items()) if quantity > 0.0]
            for held_tile, quantity in held:
                used = min(wanted, quantity)
                moves.append(GoodsMove(state, EDGE_CONSUMPTION, good, held_tile, used, "state stores used"))
                wanted -= used
            if wanted <= 0.0 or good not in area_map.goods():
                continue
            area = view.area_of(good, tile)
            order_book.setdefault((good, area), ([], []))[0].append(
                Bid(state, good, area, tile, 0.0, wanted, price, 1.0, wanted * price))   # a fixed sum to spend: unit elastic
    record.book.move_many(moves)


def close_year(setup, record, ledger, tax_received: float) -> None:
    """What the state bought is used up; what it took in this year sets next year's revenue."""
    state = setup.state_agent
    bought: Dict[Tuple[str, str], float] = {}
    for fill in ledger.buy_fills.get(state, []):
        bought[(fill.good, fill.tile)] = bought.get((fill.good, fill.tile), 0.0) + fill.quantity
    moves = []
    for (good, tile), quantity in sorted(bought.items()):
        used = min(quantity, record.book.stock(state, good, tile))
        if used > 0.0:
            moves.append(GoodsMove(state, EDGE_CONSUMPTION, good, tile, used, "state purchases used"))
    record.book.move_many(moves)
    record.state_budget.revenue = tax_received + ledger.sales_in.get(state, 0.0)
