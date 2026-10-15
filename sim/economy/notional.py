"""Prices of goods that have not traded lately: which goods those are, and what they would cost to make.

A remembered price is a market's only while the market keeps clearing. A good whose markets have not
cleared for a while (or never did) has only an estimate: the opening price, or the last one. Where a
recipe makes it, the estimate follows the cost of a run at today's input prices and wages, so it moves
with the economy. Where nothing makes it, the last price stays, marked stale. These never feed back
into what agents plan from (the memory's prices); they are what the game is shown.
"""
import math
from typing import Dict, Set, Tuple

from sim.constants import declare

from . import unit_cost
from .market_memory import KEY_SEPARATOR, MarketMemory
from .national_prices import national_prices
from .recipes import input_depth_order

RECENT_TRADE_YEARS = declare(
    "RECENT_TRADE_YEARS", 2, kind="temporary_heuristic",
    unit="years since a market last cleared", source=None, confidence="D",
    why="A good's price counts as a market price, and counts in the price index, only while one of its "
        "markets cleared within this many years. A thin market trades in alternate years, so one year "
        "would drop it too eagerly; how long a gap makes a price stale has no measured basis.")

THIN_MARKET_SHARE_OF_OPENING_DEMAND = declare(
    "THIN_MARKET_SHARE_OF_OPENING_DEMAND", 0.1, kind="temporary_heuristic",
    unit="share of the opening's yearly quantity of a good", source=None, confidence="D",
    why="A good whose markets together trade less than this share of what the opening economy wanted of it "
        "has no national market: its price is shown blended toward what it costs to make, by how much of "
        "that share it trades. Where the line sits has no measured basis.")


def recently_traded_goods(memory: MarketMemory) -> Set[str]:
    """Goods with a market that cleared within RECENT_TRADE_YEARS."""
    recent = set()
    for key, age in memory.trade_age.items():
        if age <= RECENT_TRADE_YEARS:
            recent.add(key.split(KEY_SEPARATOR, 1)[0])
    return recent


def mean_wages(memory: MarketMemory) -> Dict[str, float]:
    by_trade: Dict[str, list] = {}
    for key, wage in memory.wages.items():
        by_trade.setdefault(key.split(KEY_SEPARATOR, 1)[0], []).append(wage)
    return {trade: math.fsum(rows) / len(rows) for trade, rows in by_trade.items()}


def notional_prices(setup, record, market=None) -> Dict[str, float]:
    """Cost per unit of the cheapest recipe making each good that has not traded lately, at the live
    prices of its inputs, the live wages and interest rate; a joint run's cost is shared among its
    outputs by value. A good is priced after the goods it is made from, so a chain of untraded goods
    follows its inputs. A good whose cheapest maker cannot be priced is left out."""
    market = national_prices(record) if market is None else market
    return _estimated_prices(setup, record, market, untraded=True, thin=False)


def _estimated_prices(setup, record, market, untraded: bool, thin: bool) -> Dict[str, float]:
    """Each good's estimate where the market's own price does not stand for it, goods taken in input-depth
    order so a good costed from its inputs sees their estimates: `untraded` goods at what they cost to make,
    and (`thin`) recently traded goods the opening wanted in bulk and the markets trade a sliver of, blended
    toward their making cost by how much of THIN_MARKET_SHARE_OF_OPENING_DEMAND they trade."""
    memory = record.memory
    recent = recently_traded_goods(memory)
    traded = _traded_volumes(record) if thin else {}
    wages = mean_wages(memory)
    rate = memory.rates.get(setup.currency_id, 0.0)
    live = dict(market)
    estimated: Dict[str, float] = {}
    for good in input_depth_order(setup.recipes):
        if good not in recent:
            if not untraded:
                continue
            cost = cheapest_cost(setup, good, live, wages, rate)
            if cost is not None:
                estimated[good] = live[good] = cost
            continue
        wanted = record.opening_basket.get(good, 0.0)
        if not thin or wanted <= 0.0:
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
    it traded last year, so a market that has dried up does not stand for the good on its remembered volume."""
    traded: Dict[str, float] = {}
    for key, usual in (record.memory.volume_weights or record.volumes).items():
        good = key.split(KEY_SEPARATOR, 1)[0]
        traded[good] = traded.get(good, 0.0) + min(usual, record.volumes.get(key, usual))
    return traded


def making_costs(setup, record) -> Dict[str, float]:
    """What each good costs to make by its cheapest recipe at the live prices and wages, traded or not."""
    memory = record.memory
    live = national_prices(record)
    wages = mean_wages(memory)
    rate = memory.rates.get(setup.currency_id, 0.0)
    costs: Dict[str, float] = {}
    for good in input_depth_order(setup.recipes):
        best = cheapest_cost(setup, good, live, wages, rate)
        if best is not None:
            costs[good] = best
    return costs


def cheapest_cost(setup, good, live, wages, rate):
    """Cost per unit of the cheapest recipe making `good`, a joint run's cost shared by value; None when
    no recipe making it can be priced."""
    best = math.inf
    for recipe in setup.recipes.values():
        quantity = recipe.outputs.get(good, 0.0)
        if quantity <= 0.0:
            continue
        cost = (unit_cost.variable_cost_per_run(recipe, live, wages)
                + unit_cost.capital_charge_per_run(recipe, live, wages, rate))
        if not math.isfinite(cost):
            continue
        values = {made: amount * live.get(made, 0.0) for made, amount in recipe.outputs.items()}
        total_value = math.fsum(values.values())
        share = values[good] / total_value if total_value > 0.0 else 1.0 / len(recipe.outputs)
        best = min(best, cost * share / quantity)
    return best if math.isfinite(best) and best > 0.0 else None


def shown_prices(setup, record, market=None) -> Tuple[Dict[str, float], Set[str]]:
    """(prices, stale goods) the game is shown. A recently traded good shows its market price, except one
    the markets trade only a sliver of, which shows near what it costs to make (see `_estimated_prices`).
    An untraded good somebody can make shows what it costs to make; one nobody can make keeps its last
    price. Both kinds are listed as stale: not a price a market has set lately."""
    prices = dict(national_prices(record) if market is None else market)
    stale = set(prices) - recently_traded_goods(record.memory)
    prices.update(_estimated_prices(setup, record, prices, untraded=True, thin=True))
    return prices, stale


def thin_market_prices(setup, record, market) -> Dict[str, float]:
    """The price of each recently traded good that the opening economy wanted in bulk but whose markets
    together trade only a sliver of it: the market price blended toward the cost of making it, in the
    share the trade falls short of THIN_MARKET_SHARE_OF_OPENING_DEMAND. A good nobody can make, or the
    opening did not want, keeps its market price."""
    return _estimated_prices(setup, record, market, untraded=False, thin=True)
