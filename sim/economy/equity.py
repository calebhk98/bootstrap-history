"""What the households own of the firms: the net worth of each producer, shared by ownership share.

A producer's dividends reach its owner's tile and are split across the tile's cohorts by ownership share
(`ownership.spread`); the claim on its net worth (cash, plant at what it would cost to build now and stock, less
what it owes) is split the same way. Where a producer has sold shares (shares.py) the holders of its shares own
their part of that worth and the owner's tile the rest.
`holdings` is the one read of it; the market view answers `equity` from it, so a household counts what it
owns of the firms among the wealth it wants to hold.
"""
import math
from typing import Dict, Optional, Tuple

from . import credit_claims, producers, unit_cost
from .types import AgentId


def plant_value(producer, recipe, view, per_run: Optional[Dict[Tuple[str, str], float]] = None) -> float:
    """The producer's plant at what it would cost to build now. `per_run` keeps the cost of a run's plant by (recipe, tile)
    across the producers of one pass."""
    if recipe.plant_life_years <= 0.0:
        return 0.0
    if per_run is None:
        return producer.capacity_runs * _plant_per_run(producer, recipe, view)
    key = (recipe.recipe_id, producer.tile)
    if key not in per_run:
        per_run[key] = _plant_per_run(producer, recipe, view)
    return producer.capacity_runs * per_run[key]


def _plant_per_run(producer, recipe, view) -> float:
    return unit_cost.plant_value_per_run(recipe, producers.live_input_prices(producer, recipe, view),
                                         producers.live_wages(producer, recipe, view))


def inventory_value(record, producer, view, prices: Optional[Dict[Tuple[str, str], Optional[float]]] = None) -> float:
    """The goods the producer holds, at the prices it sees (Eurace@Unibi counts the inventory in its assets). `prices` keeps the
    price of a good on a tile across the producers of one pass. Summed exactly, so the order the book holds goods in is no matter."""
    held = record.book.goods_of(producer.agent_id)
    if not held:
        return 0.0
    if prices is None:
        prices = {}
    tile = producer.tile
    terms = []
    for good, by_tile in held.items():
        key = (good, tile)
        price = prices[key] if key in prices else prices.setdefault(key, view.price(good, view.area_of(good, tile)))
        if price is not None and price > 0.0:
            quantities = [quantity for quantity in by_tile.values() if quantity > 0.0]
            if quantities:
                terms.append(price * (quantities[0] if len(quantities) == 1 else math.fsum(quantities)))
    return terms[0] if len(terms) == 1 else math.fsum(terms)


def firm_assets(producer, recipe, cash: float, stock: float, view) -> float:
    """Cash, plant at replacement cost and the stock held (Eurace@Unibi, Financial_Management,
    Firm_compute_balance_sheet: the assets include the inventory)."""
    return cash + plant_value(producer, recipe, view) + stock


def producer_worths(setup, record, view) -> Dict[AgentId, float]:
    """The net worth of each producer a household owns and that has plant. A view that keeps them (`CreditView.kept_worths`)
    builds them once, for the households' equity and the portfolio trading alike; the result is read only."""
    kept = getattr(view, "kept_worths", None)
    return _built_worths(setup, record, view) if kept is None else kept(lambda: _built_worths(setup, record, view))


def _built_worths(setup, record, view) -> Dict[AgentId, float]:
    """The plant's cost per run and the prices of the goods held are read once per (recipe, tile) and (good, tile)
    over all the producers."""
    money = setup.currency_id
    debts = credit_claims.debts_by_borrower(record.credit.loans, money)
    balance = record.book.balance
    cohorts = record.cohorts
    per_run: Dict[Tuple[str, str], float] = {}
    prices: Dict[Tuple[str, str], Optional[float]] = {}
    worths: Dict[AgentId, float] = {}
    for producer_id, producer in sorted(record.producers.items()):
        if producer.owner not in cohorts or producer.capacity_runs <= 0.0:
            continue
        recipe = setup.recipes[producer.recipe_id]
        assets = (balance(producer_id, money) + plant_value(producer, recipe, view, per_run)
                  + inventory_value(record, producer, view, prices))
        worths[producer_id] = max(0.0, assets - debts.get(producer_id, 0.0))
    return worths


def holdings(setup, record, view) -> Dict[AgentId, float]:
    """Each cohort's share of the net worth of the producers its tile's owners hold. What holders of a producer's
    shares own is valued at the share index price (household_portfolio.py), the price their portfolio orders trade at."""
    shares_of_tile: Dict[str, Tuple[float, list]] = {}      # tile -> (sum of ownership shares, [(cohort id, share)])
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        total, parts = shares_of_tile.setdefault(cohort.tile, (0.0, []))
        shares_of_tile[cohort.tile] = (total + cohort.ownership_share, parts)
        parts.append((cohort.agent_id, cohort.ownership_share))
    factor = record.capital_markets.capital.share_price_factor
    outside_shares = record.capital_markets.shares
    held: Dict[AgentId, float] = {}
    for producer_id, worth in producer_worths(setup, record, view).items():
        owner = record.cohorts[record.producers[producer_id].owner]
        outside = outside_shares.get(producer_id)
        if outside:                      # what holders of its shares own is theirs, not the owner tile's
            for holder, part in outside.items():
                held[holder] = held.get(holder, 0.0) + part * worth * factor
            worth *= max(0.0, 1.0 - sum(outside.values()))
        total, parts = shares_of_tile[owner.tile]
        for agent, share in parts:      # the tile's rent and profit income split by what each class owns
            held[agent] = held.get(agent, 0.0) + (worth * share / total if total > 0.0 else 0.0)
    return held
