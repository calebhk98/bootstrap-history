"""The state as a buyer: each year it spends its revenue and part of any cash above its reserve, bidding
for hours in the labour market and for goods in the goods markets like anyone else, and covers a
shortfall by the policy's order (state_finance.py). Goods already in its stores are used before it buys."""
import math
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Tuple

from sim.constants import declare

from . import currency, households_basket, state_finance, trade_wages
from .goods_order_tables import STATE
from .home_scope import home_working_by_tile
from .labour_results_table import bought_value
from .order_rows import OrderRows
from .priced_need_list import priced_needs_of
from .setup import labour_area
from .state_wage_ceiling import WAGE_CEILING_MULTIPLE
from .labour_bid_sink import BidFigures, bid_objects, put_bids
from .types import EDGE_CONSUMPTION, GoodsMove, LabourBid

STATE_MAX_SHARE_OF_TILE_HOURS = declare(
    "STATE_MAX_SHARE_OF_TILE_HOURS", 0.3, kind="temporary_heuristic",
    unit="share of a tile's working hours the state will bid for",
    source=None, confidence="D",
    why="Stands in for the size of the state's establishment (how many soldiers and officials it can "
        "house, drill and supervise), which the engine does not yet supply.")


@dataclass
class StateBudget:
    OWNERS: ClassVar[Tuple[str, ...]] = ("state_budget",)   # the sim/economy modules allowed to write this (tools/check_record_owners.py)
    revenue: float = 0.0                 # money the state took in last year (taxes and sales)
    wage_budget: float = 0.0             # this year's plan
    goods_budget: float = 0.0
    deficit: float = 0.0
    financed: Dict[str, float] = field(default_factory=dict)   # what each method supplied this year
    issued_total: float = 0.0
    unplanned_cash: float = 0.0          # cash left after the plan and the reserve: what the store may buy with
    held_back: float = 0.0               # cash the plan keeps off its lines: the reserve and the unplanned cash
    need_wanted: Dict[str, float] = field(default_factory=dict)   # goods the lines bid for, so the rest bought is store
    expected_inflation: float = 0.0      # what the treasury expects of prices, as households do
    last_price_level: float = 0.0        # the chained price level (across rebases) when it last updated that expectation
    real_programme: bool = False         # a stated real spending target: its goods are bought as quantities, not as a sum

    def cut_goods_budget(self, amount: float) -> None:
        """The goods line falls by `amount`."""
        self.goods_budget -= amount


def plan_year(setup, record, view, labour_bids: List[LabourBid]) -> None:
    """Fix this year's spending and its financing, and add the state's bids for hours to `labour_bids`."""
    policy, budget = setup.state_policy, record.state_budget
    money, state = setup.currency_id, setup.state_agent
    cash = record.book.balance(state, money)
    budget.real_programme = False
    reserve = policy.reserve_years_of_revenue * budget.revenue
    spendable = min(cash, budget.revenue + policy.cash_spend_share * max(0.0, cash - budget.revenue - reserve))
    planned = spendable
    budget.unplanned_cash = max(0.0, cash - spendable - reserve)
    budget.held_back = reserve + budget.unplanned_cash
    if policy.real_spending_target > 0.0:
        # a stated programme is paid from every coin on hand first, then financed
        planned = policy.real_spending_target * view.opening_wage_level(money)   # the target is in opening-year money; the level survives the rebase
        budget.real_programme = True
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
    put_bids(labour_bids, wage_bid_figures(setup, record, view, budget.wage_budget))


def wages_paid(labour_results, state) -> float:
    """What the state paid for the hours it bought: its bought hours at their wage, over every trade's result."""
    return bought_value(labour_results, state)


def lapse_unspent_wages(budget: StateBudget, paid: float) -> None:
    """A stated real programme that could not hire the hours it planned for (the labour market did not clear at its
    bids) spends the rest on goods: a shortage of hired labour must not leave the coin it printed in the purse.
    A budget that is not a programme keeps its unspent cash for the next year's plan."""
    unspent = budget.wage_budget - paid
    if not budget.real_programme or unspent <= 0.0:
        return
    budget.wage_budget = paid
    budget.goods_budget += unspent


def _trades(setup):
    trades = [trade for trade in setup.state_policy.trades if trade in setup.trades]
    return trades or [setup.unskilled_trade]


def wage_labour_bids(setup, record, view, wage_budget: float) -> List[LabourBid]:
    """The home state's bids for hours as records (an edge: the workforce's figures)."""
    return bid_objects(wage_bid_figures(setup, record, view, wage_budget))


def wage_bid_figures(setup, record, view, wage_budget: float) -> List[BidFigures]:
    """The home state's bids for hours, spread over the home cohorts' tiles and the trades it hires: (employer, trade, area, hours,
    maximum wage) each."""
    if wage_budget <= 0.0:
        return []
    working = home_working_by_tile(setup, record)
    total_working = math.fsum(working.values())
    if total_working <= 0.0:
        return []
    trades = _trades(setup)
    bids = []
    for trade in trades:
        for tile, people in sorted(working.items()):
            area = labour_area(tile)
            wage = trade_wages.wage_in_view(setup, view, trade, area)
            ceiling = wage * WAGE_CEILING_MULTIPLE
            hours = min(wage_budget / len(trades) * people / total_working / ceiling,
                        people * setup.working_hours_per_year * STATE_MAX_SHARE_OF_TILE_HOURS)
            if hours > 0.0:
                bids.append((setup.state_agent, trade, area, hours, ceiling))
    return bids


def goods_bids(setup, record, view, area_map, order_book, kept=None) -> None:
    """Spend the goods budget across the basket's needs by their weights and each need's goods by the
    household mix (a stated real programme buys those quantities whatever the price, up to the budget; otherwise
    a dearer good draws less, as a household's bid does); stores already held are used up first and cost nothing, except the durable store
    (`kept`, by good), which the lines leave alone."""
    budget = record.state_budget
    budget.need_wanted = {}
    kept = dict(kept or {})
    if budget.goods_budget <= 0.0:
        return
    tile = setup.capital_tile
    basket = setup.basket_for(tile)
    priced = priced_needs_of(households_basket.tile_need_prices(setup, view, tile))
    weight_total = math.fsum(spec.budget_weight for spec, _index, _first, _end in priced.blocks())
    if weight_total <= 0.0:
        return
    state = setup.state_agent
    moves = []
    rows = OrderRows(order_book, STATE)
    state_held = record.book.goods_held(state)      # the moves are posted after the loop, so the stores stay as read
    names, prices, shares = priced.columns.names, priced.columns.price, priced.columns.share
    for spec, _index, first, end in priced.blocks():
        need_budget = budget.goods_budget * spec.budget_weight / weight_total
        for row in range(first, end):
            good, price, share = names[row], prices[row], shares[row]
            wanted = need_budget * share / price
            held = [(held_tile, quantity) for held_tile, quantity in
                    sorted(state_held.get(good, {}).items()) if quantity > 0.0]
            for held_tile, quantity in held:
                reserved = min(quantity, kept.get(good, 0.0)) if held_tile == tile else 0.0
                used = min(wanted, quantity - reserved)
                moves.append(GoodsMove(state, EDGE_CONSUMPTION, good, held_tile, used, "state stores used"))
                wanted -= used
            if wanted <= 0.0 or good not in area_map.goods():
                continue
            budget.need_wanted[good] = budget.need_wanted.get(good, 0.0) + wanted
            area = view.area_of(good, tile)
            rows.bid(state, good, area, tile, wanted if budget.real_programme else 0.0,
                     0.0 if budget.real_programme else wanted, price, basket.substitution, wanted * price)
    record.book.move_many(moves)
    rows.write()


def close_year(setup, record, ledger, tax_received: float) -> None:
    """What the state bought for its lines is used up (not what it bought to hold); what it took in this
    year sets next year's revenue."""
    state = setup.state_agent
    bought: Dict[Tuple[str, str], float] = {}
    for fill in ledger.buy_fills.get(state, []):
        bought[(fill.good, fill.tile)] = bought.get((fill.good, fill.tile), 0.0) + fill.quantity
    lines_left = dict(record.state_budget.need_wanted)   # the lines' bids clear before the store's (priority)
    moves = []
    for (good, tile), quantity in sorted(bought.items()):
        quantity = min(quantity, lines_left.get(good, 0.0))
        lines_left[good] = lines_left.get(good, 0.0) - quantity
        used = min(quantity, record.book.stock(state, good, tile))
        if used > 0.0:
            moves.append(GoodsMove(state, EDGE_CONSUMPTION, good, tile, used, "state purchases used"))
    record.book.move_many(moves)
    record.state_budget.revenue = tax_received + ledger.sales_in.get(state, 0.0)
    memory = record.memory   # the level that survives a rebase: opening-year money per money now
    level = memory.opening_wage_level(setup.currency_id) if memory.price_levels.get(setup.currency_id) else None
    budget = record.state_budget
    if level and budget.last_price_level > 0.0:
        budget.expected_inflation = currency.update_expected_inflation(budget.expected_inflation,
                                                                       level / budget.last_price_level - 1.0)
    budget.last_price_level = level or budget.last_price_level
