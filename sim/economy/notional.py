"""Prices of goods that have not traded lately: which goods those are, and what they would cost to make.

A remembered price is a market's only while the market keeps clearing. A good whose markets have not
cleared for a while (or never did) has only an estimate: the opening price, or the last one. Where a
recipe makes it, the estimate follows the cost of a run at today's input prices and wages, so it moves
with the economy. Where nothing makes it, the last price stays, marked stale. The economy's own agents plan
from the memory's prices, not these; the engine's agents are shown these (`prices_at`) and plan from them, and
`making_costs` steers the price a thin or empty market remembers.
"""
import math
from typing import Dict, Optional, Set, Tuple

import numpy

from sim.constants import declare

from . import trade_wages, unit_cost
from .market_memory import KEY_SEPARATOR, PRICE_REMEMBERED, PRICE_SMOOTHED_TRADE, RECENT_TRADE_YEARS, MarketMemory
from .market_column_kernels import add_in_order_by_group
from .market_store import figures_for
from .national_prices import national_prices, national_wages, usual_volumes
from .recipes import input_depth_order, recipes_making

KIND_MAKING_COST_ESTIMATE = "making_cost_estimate"   # what the cheapest recipe costs at today's prices; nothing traded lately
KIND_THIN_TRADE_BLEND = "thin_trade_blend"           # a market price blended toward making cost; the market trades a sliver
KIND_REMEMBERED = PRICE_REMEMBERED                 # the last price shown, nothing makes the good and nothing traded lately

THIN_MARKET_SHARE_OF_OPENING_DEMAND = declare(
    "THIN_MARKET_SHARE_OF_OPENING_DEMAND", 0.1, kind="temporary_heuristic",
    unit="share of the opening's yearly quantity of a good", source=None, confidence="D",
    why="A good whose markets together trade less than this share of what the opening economy wanted of it "
        "has no national market: its price is shown blended toward what it costs to make, by how much of "
        "that share it trades. Where the line sits has no measured basis.")


def recently_traded_goods(memory: MarketMemory) -> Set[str]:
    """Goods with a market that cleared within RECENT_TRADE_YEARS."""
    return memory.goods_traded_within(RECENT_TRADE_YEARS)


def _estimated_prices(setup, record, market, thin: bool, wages: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """Each good's estimate where the market's own price does not stand for it, goods taken in input-depth
    order so a good costed from its inputs sees their estimates: untraded goods at what they cost to make,
    and (`thin`) recently traded goods the opening wanted in bulk and the markets trade a sliver of, blended
    toward their making cost by how much of THIN_MARKET_SHARE_OF_OPENING_DEMAND they trade."""
    memory = record.memory
    recent = recently_traded_goods(memory)
    traded = _traded_volumes(record) if thin else {}
    wages = costing_wages(setup, record) if wages is None else wages
    rate = memory.rates[setup.currency_id]
    live = dict(market)
    estimated: Dict[str, float] = {}
    for good in input_depth_order(setup.recipes):
        if good not in recent:
            cost = cheapest_cost(setup, good, live, wages, rate)
            if cost is not None:
                estimated[good] = live[good] = cost
            continue
        wanted = record.goods.opening_basket.get(good, 0.0)
        if not thin or wanted <= 0.0 or good not in live:     # a good traded only outside this country's markets has no price here
            continue
        depth = min(1.0, traded.get(good, 0.0) / (THIN_MARKET_SHARE_OF_OPENING_DEMAND * wanted))
        if depth >= 1.0:
            continue
        cost = cheapest_cost(setup, good, live, wages, rate)
        if cost is not None:
            estimated[good] = live[good] = depth * live[good] + (1.0 - depth) * cost
    return estimated


def _traded_volumes(record) -> Dict[str, float]:
    """What each good's markets trade, a market counting for the smaller of what it usually trades and what
    it traded last year, so a market that has dried up does not stand for the good on its remembered volume. The memory's own
    usual volumes are read from the table's columns, added in the order the markets entered the store."""
    usual = usual_volumes(record)
    if usual is not record.memory.volume_weights:
        return _traded_volumes_by_key(record, usual)
    markets = record.memory.tables.goods_table
    rows = usual.rows()
    last_year = numpy.array(figures_for(record.goods.volumes, list(usual), 0.0), dtype=float)
    totals, first_seen, appeared = add_in_order_by_group(markets.first[rows], numpy.minimum(markets.volume_weight[rows], last_year),
                                                         len(record.memory.tables.goods))
    names = record.memory.tables.goods.names
    return {names[good]: totals[good].item() for good in first_seen[:appeared].tolist()}


def _traded_volumes_by_key(record, usual) -> Dict[str, float]:
    """`_traded_volumes` over usual volumes that are not the memory's own (this year's volumes, before any is remembered)."""
    traded: Dict[str, float] = {}
    for key, volume in usual.items():
        good = key.split(KEY_SEPARATOR, 1)[0]
        traded[good] = traded.get(good, 0.0) + min(volume, record.goods.volumes.get(key, 0.0))
    return traded


def costing_wages(setup, record) -> Dict[str, float]:
    """The wage per hour of every trade of the setup for costing a recipe: the national wage where the memory holds one,
    else the one wage rule (`trade_wages.priced_trade_wage`; the memory holds none for the trade in any area, so its
    opening wage at today's level), so a recipe is never unpriceable for a trade the labour core has not cleared."""
    memory = record.memory
    wages = national_wages(record)
    level = memory.opening_wage_level(setup.currency_id)
    return {trade: wages[trade] if trade in wages else trade_wages.priced_trade_wage(
        setup, trade, None, wages.get(setup.unskilled_trade), level, memory.holds_wage_for(trade)) for trade in sorted(setup.trades)}


def making_costs(setup, record) -> Dict[str, float]:
    """What each good costs to make by its cheapest recipe at the live prices and wages, traded or not."""
    memory = record.memory
    live = national_prices(record)
    wages = costing_wages(setup, record)
    rate = memory.rates[setup.currency_id]
    costs: Dict[str, float] = {}
    for good in input_depth_order(setup.recipes):
        best = cheapest_cost(setup, good, live, wages, rate)
        if best is not None:
            costs[good] = best
    return costs


def cheapest_cost(setup, good, live, wages, rate):
    """Cost per unit of the cheapest recipe making `good` at the prices `live` and the live rate
    (`unit_cost.full_cost_per_unit`; no maker or site is named, so yield 1 and no rent); None when no recipe making it
    can be priced."""
    best = min((unit_cost.full_cost_per_unit(recipe, good, live, live, wages, rate)
                for recipe in recipes_making(setup.recipes, good)), default=math.inf)
    return best if math.isfinite(best) and best > 0.0 else None


def shown_prices_with_kinds(setup, record, market=None, wages=None, remembered=None) -> Tuple[Dict[str, float], Set[str], Dict[str, str]]:
    """(prices, stale goods, kind of each good's price) the game is shown. A recently traded good shows its
    market price, except one the markets trade only a sliver of, which shows near what it costs to make (see
    `_estimated_prices`). An untraded good somebody can make shows what it costs to make; one nobody can make
    keeps its last price. Stale goods are not a price a market has set lately: their kind says whether it is a
    making-cost estimate, a quote (named by what it is) or the last price. `wages` (`costing_wages`) and `remembered`
    (`MarketMemory.price_kinds_by_good`) are the figures of the record that a caller asking for several scopes works out once."""
    prices = dict(national_prices(record) if market is None else market)
    stale = set(prices) - recently_traded_goods(record.memory)
    estimated = _estimated_prices(setup, record, prices, thin=True, wages=wages)
    prices.update(estimated)
    remembered = record.memory.price_kinds_by_good() if remembered is None else remembered
    kinds = {}
    for good in prices:
        if good in estimated:
            kinds[good] = KIND_MAKING_COST_ESTIMATE if good in stale else KIND_THIN_TRADE_BLEND
        else:
            kinds[good] = remembered.get(good, PRICE_SMOOTHED_TRADE if good not in stale else KIND_REMEMBERED)
    return prices, stale, kinds


def shown_prices(setup, record, market=None) -> Tuple[Dict[str, float], Set[str]]:
    """(prices, stale goods) the game is shown; see `shown_prices_with_kinds`."""
    prices, stale, _kinds = shown_prices_with_kinds(setup, record, market)
    return prices, stale
