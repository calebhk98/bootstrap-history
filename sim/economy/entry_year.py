"""The year's entry: the markets with unmet demand become new producers (entry.py), each owned by the
richest household of its tile (newcomers to a recipe already worked on the tile join that producer's
capacity), which stakes part of its cash as working cash; one with plant to build
asks the credit market for it, and its capacity grows as the plant goods arrive. Owners also put working
cash back into paying producers that ran out of it."""
import math
from typing import Dict, Tuple

from . import credit, entry_practice, location, ownership, practice, sites, unit_cost
from .entry_backed import unfilled_at_cost
from .entry_margin import margin_entry_plans
from .entrant_rent import site_rent_per_run
from .entry_trial import trial_entry_plans
from .entry import (ENTRANT_OWNER_STAKE_SHARE, UnmetDemand, entrant_loan, entry_plans, gap_beyond_spare,
                    producers_to_close, restake)
from .producers import Producer, expected_output_prices, live_input_prices, live_wages
from .producers_close import working_capital_target
from .market_memory import market_key
from .setup import recipe_tile_key
from .types import GoodsMove, LoanRequest, Transfer
from .replaced import replaced


def open_entrants(setup, record, view, area_map, unmet_by_market: Dict[Tuple[str, str], float],
                  carriage=None, bids_by_market=None) -> int:
    """Start the year's new producers; returns how many started. With the carriage table a newcomer is
    sited by location.entry_siting; without it one is built from the setup (slower on a large map). With
    the year's bids, a market whose expected price stays above its entry price draws newcomers
    (entry_margin.py) and a market with buyers and no maker draws a trial newcomer (entry_trial.py)."""
    spare = _spare_output(setup, record, view)
    unmet = {}
    for (good, area_id), quantity in sorted(unmet_by_market.items()):
        area = next((each for each in area_map.areas(good) if each.area_id == area_id), None) \
            if good in area_map.goods() else None
        gap = gap_beyond_spare(quantity, spare.get((good, area_id), 0.0))
        if area is not None and gap > 0.0:
            unmet[(good, area_id)] = UnmetDemand(good, area_id, area.anchor_tile, gap)
    money = setup.currency_id
    started = 0
    by_limits = sites.limits_by_recipe(setup.site_limits)
    siting = location.entry_siting(setup, record, view, area_map, carriage or _carriage(setup))
    traded = _traded_volume(record, view, area_map)
    plans = entry_plans(setup.recipes, view, unmet, record.land_rent, setup.land_per_run, traded, siting,
                        unfilled_at_cost(setup, record, view, area_map, bids_by_market, traded),
                        lambda recipe_id, tile: site_rent_per_run(setup, record, view, recipe_id, tile),
                        entry_practice.crews_of_recipe(record.producers))
    if bids_by_market:
        planned = tuple((plan.good, view.area_of(plan.good, plan.tile)) for plan in plans)
        plans += margin_entry_plans(setup, record, view, area_map, bids_by_market, planned, siting)
        planned += tuple((plan.good, view.area_of(plan.good, plan.tile)) for plan in plans)
        plans += trial_entry_plans(setup, record, view, area_map, bids_by_market, planned, siting)
    for plan in plans:
        recipe = setup.recipes[plan.recipe_id]
        key = recipe_tile_key(plan.recipe_id, plan.tile)
        producer_id = "producer:" + key
        builds_plant = recipe.plant_life_years > 0.0 and bool(recipe.plant_goods)
        # each producer stands for the tile's workshops of one recipe: newcomers join its capacity and its workshop count
        producer = record.producers.get(producer_id)
        if producer is None:
            owner = ownership.owner_cohort(record, plan.tile)
            if owner is None:
                continue
            producer = Producer(agent_id=producer_id, owner=owner, recipe_id=plan.recipe_id, tile=plan.tile,
                                capacity_runs=0.0, expected_sales=plan.runs,
                                crew_runs=practice.entrant_crew_runs(recipe, [each.crew_runs for each in record.producers.values()
                                                                              if each.recipe_id == plan.recipe_id]),
                                yield_factor=sites.yield_at(recipe, plan.tile, by_limits,
                                                            setup.yield_factor_by_recipe_tile.get(key, 1.0)))
        elif record.expansion_runs.get(producer_id, 0.0) > 0.0:     # a working-capital loan builds no plant
            continue                                    # plant it already asked for is still to come
        if not builds_plant:
            producer = replaced(producer, capacity_runs=producer.capacity_runs + plan.runs,
                                workshops=producer.workshops + 1)
        record.producers[producer_id] = producer
        started += 1
        inputs, wages = live_input_prices(producer, recipe, view), live_wages(producer, recipe, view)
        stake = min(working_capital_target(practice.recipe_for(recipe, producer.crew_runs), plan.runs, inputs, wages),
                    ENTRANT_OWNER_STAKE_SHARE * max(0.0, record.book.balance(producer.owner, money)))
        if stake > 0.0:
            record.book.transfer(Transfer(producer.owner, producer_id, money, stake, "stake in a new workshop"))
        if builds_plant:
            per_run = unit_cost.plant_value_per_run(recipe, inputs, wages)
            loan = entrant_loan(per_run * plan.runs, stake) if per_run > 0.0 and math.isfinite(per_run) else 0.0
            if loan > 0.0:
                record.loan_requests.append(LoanRequest(producer_id, money, loan, credit.earnable_rate(plan.yearly_return),
                                                        recipe.plant_life_years, loan, "enter"))
                record.expansion_runs[producer_id] = loan / per_run
    return started


def _carriage(setup):
    return setup.carriage_table()


def _traded_volume(record, view, area_map):
    """What a good's market (on a tile) carried last year; None for a good with no market."""
    goods = set(area_map.goods())

    def traded(good, tile):
        return record.volumes.get(market_key(good, view.area_of(good, tile)), 0.0) if good in goods else None
    return traded


def restake_owners(setup, record, view) -> None:
    """Owners put working cash back into producers whose runs pay but that ran out of it."""
    money = setup.currency_id
    rate = view.interest_rate(money)
    # an owner risks at most the stake share of its cash a year, across all the producers it owns
    budget = {}
    for producer_id, producer in sorted(record.producers.items()):
        if producer.capacity_runs <= 0.0:
            continue
        shortfall = producer.cash_target - record.book.balance(producer_id, money)
        if shortfall <= 0.0:
            continue
        recipe = setup.recipes[producer.recipe_id]
        pays = unit_cost.return_on_capital(recipe, expected_output_prices(producer, recipe, view) or {},
                                           live_input_prices(producer, recipe, view),
                                           live_wages(producer, recipe, view),
                                           producer.land_rent_per_run) > rate
        if producer.owner not in budget:
            budget[producer.owner] = ENTRANT_OWNER_STAKE_SHARE * max(0.0, record.book.balance(producer.owner, money))
        amount = min(restake(shortfall, record.book.balance(producer.owner, money), pays), budget[producer.owner])
        if amount > 0.0:
            budget[producer.owner] -= amount
            record.book.transfer(Transfer(producer.owner, producer_id, money, amount, "owner's stake"))


def close_idle_producers(setup, record) -> int:
    """Close producers with nothing left to do (entry.producers_to_close): their cash and any goods they
    still hold go to their owner."""
    money = setup.currency_id
    debtors = {loan.borrower for loan in record.loans}
    closing = producers_to_close(record.producers, set(record.expansion_runs), debtors)
    for producer_id in closing:
        owner = record.producers[producer_id].owner
        cash = record.book.balance(producer_id, money)
        if cash > 0.0:
            record.book.transfer(Transfer(producer_id, owner, money, cash, "a closed producer's cash"))
        moves = [GoodsMove(producer_id, owner, good, tile, quantity, "a closed producer's stock")
                 for good, tiles in sorted(record.book.holdings(producer_id)["goods"].items())
                 for tile, quantity in sorted(tiles.items()) if quantity > 0.0]
        if moves:
            record.book.move_many(moves)
        del record.producers[producer_id]
    return len(closing)


def _spare_output(setup, record, view) -> Dict[Tuple[str, str], float]:
    """Output (good, area) the market's makers could have added from idle capacity last year."""
    spare: Dict[Tuple[str, str], float] = {}
    for producer in sites.in_id_order(record.producers):
        recipe = setup.recipes[producer.recipe_id]
        # capacity waiting on a plant loan counts too, so one gap does not bring a newcomer every year
        idle_runs = (producer.capacity_runs - max(0.0, producer.last_runs)
                     + record.expansion_runs.get(producer.agent_id, 0.0))
        if idle_runs <= 0.0:
            continue
        for good, made in recipe.outputs.items():
            key = (good, view.area_of(good, producer.tile))
            spare[key] = spare.get(key, 0.0) + idle_runs * made * producer.yield_factor
    return spare
