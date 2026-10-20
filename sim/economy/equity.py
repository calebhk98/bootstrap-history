"""What the households own of the firms: the net worth of each producer, shared by ownership share.

A producer's dividends reach its owner's tile and are split across the tile's cohorts by ownership share
(`ownership.spread`); the claim on its net worth (cash and plant at what it would cost to build now, less
what it owes) is split the same way. Where a producer has sold shares (shares.py) the holders of its shares own
their part of that worth and the owner's tile the rest.
`holdings` is the one read of it; the market view answers `equity` from it, so a household counts what it
owns of the firms among the wealth it wants to hold.
"""
from typing import Dict

from . import credit_claims, producers, unit_cost
from .households_cohort import distribute_property_income
from .types import AgentId


def firm_net_worth(producer, recipe, cash: float, debt: float, view) -> float:
    """Cash plus plant at replacement cost less debt; a firm's owners cannot lose more than they put in."""
    plant = 0.0
    if recipe.plant_life_years > 0.0:
        plant = producer.capacity_runs * unit_cost.plant_value_per_run(
            recipe, producers.live_input_prices(producer, recipe, view), producers.live_wages(producer, recipe, view))
    return max(0.0, cash + plant - debt)


def holdings(setup, record, view) -> Dict[AgentId, float]:
    """Each cohort's share of the net worth of the producers its tile's owners hold."""
    money = setup.currency_id
    debts = credit_claims.debts_by_borrower(record.loans, money)
    cohorts_of_tile: Dict[str, list] = {}
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        cohorts_of_tile.setdefault(cohort.tile, []).append(cohort)
    held: Dict[AgentId, float] = {}
    for producer_id, producer in sorted(record.producers.items()):
        owner = record.cohorts.get(producer.owner)
        if owner is None or producer.capacity_runs <= 0.0:
            continue
        worth = firm_net_worth(producer, setup.recipes[producer.recipe_id], record.book.balance(producer_id, money),
                               debts.get(producer_id, 0.0), view)
        outside = record.shares.get(producer_id)
        if outside:                      # what holders of its shares own is theirs, not the owner tile's
            for holder, part in outside.items():
                held[holder] = held.get(holder, 0.0) + part * worth
            worth *= max(0.0, 1.0 - sum(outside.values()))
        for agent, amount in distribute_property_income(cohorts_of_tile[owner.tile], worth).items():
            held[agent] = held.get(agent, 0.0) + amount
    return held
