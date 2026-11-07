"""The year's entry: the markets with unmet demand become new producers (entry.py), each owned by the
richest household of its tile (newcomers to a recipe already worked on the tile join that producer's
capacity), which stakes part of its cash as working cash; one with plant to build
asks the credit market for it, and its capacity grows as the plant goods arrive. Owners also put working
cash back into paying producers that ran out of it."""
import math
from typing import Dict, List, Tuple

from . import producer_table
from . import credit, entry_practice, location, ownership, practice, producer_exit, sites, unit_cost
from .entry_backed import unfilled_at_cost
from .entry_margin import margin_entry_plans
from .entry_spare import idle_runs
from .entrant_rent import site_rent_per_run
from .entry_tables import EntryTables
from .entry_trial import trial_entry_plans
from .entry import (ENTRANT_OWNER_STAKE_SHARE, EntryPlan, UnmetDemand, entrant_loan, entry_plans, gap_beyond_spare,
                    producers_to_close, restake)
from .producers import Producer, expected_output_prices, live_input_prices, live_wages
from .producers_close import working_capital_target
from .market_memory import market_key
from .setup import recipe_tile_key
from .types import LoanRequest, Transfer
from .replaced import replaced
from .rates import own_rate


def year_plans(setup, record, view, area_map, unmet_by_market: Dict[Tuple[str, str], float], carriage=None,
               bids_by_market=None, arrays=None) -> List[EntryPlan]:
    """The year's entry plans, in the order they are applied: the unmet markets' (entry.py), then the margin's and the trial's
    where there are bids. See `open_entrants` for `arrays`."""
    with entry_practice.shared_crews(record.producers):
        costs = None if arrays is None else EntryTables.build(
            setup, record, view, area_map, arrays.sync(setup, record, view), carriage or _carriage(setup),
            entry_practice.crews_of_recipe(record.producers))
        spare = _spare_output(setup, record, view) if costs is None else None
        spare_grid = None if costs is None else costs.spare_output()
        unmet = {}
        areas_of: Dict[str, Dict[str, object]] = {}
        known_goods = set(area_map.goods())
        for (good, area_id), quantity in sorted(unmet_by_market.items()):
            if good not in known_goods:
                continue
            if good not in areas_of:
                areas_of[good] = {each.area_id: each for each in area_map.areas(good)}
            area = areas_of[good].get(area_id)
            if area is None:
                continue
            gap = gap_beyond_spare(quantity, spare.get((good, area_id), 0.0) if spare_grid is None else _spare_at(
                spare_grid, costs, good, area_id))
            if gap > 0.0:
                unmet[(good, area_id)] = UnmetDemand(good, area_id, area.anchor_tile, gap)
        siting = location.entry_siting(setup, record, view, area_map, carriage or _carriage(setup), costs)
        traded = _traded_volume(record, view, area_map)
        plans = entry_plans(setup.recipes, view, unmet, traded, siting,
                            unfilled_at_cost(setup, record, view, area_map, bids_by_market, traded, costs),
                            lambda recipe_id, tile: site_rent_per_run(setup, record, view, recipe_id, tile),
                            entry_practice.crews_of_recipe(record.producers), costs)
        if bids_by_market:
            planned = tuple((plan.good, view.area_of(plan.good, plan.tile)) for plan in plans)
            first_margin_plan = len(plans)
            plans += margin_entry_plans(setup, record, view, area_map, bids_by_market, planned, siting, costs)
            planned += tuple((plan.good, view.area_of(plan.good, plan.tile)) for plan in plans[first_margin_plan:])
            plans += trial_entry_plans(setup, record, view, area_map, bids_by_market, planned, siting, costs)
    return plans


def open_entrants(setup, record, view, area_map, unmet_by_market: Dict[Tuple[str, str], float],
                  carriage=None, bids_by_market=None, arrays=None) -> int:
    """Start the year's new producers; returns how many started. With the carriage table a newcomer is
    sited by location.entry_siting; without it one is built from the setup (slower on a large map). With
    the year's bids, a market whose expected price stays above its entry price draws newcomers
    (entry_margin.py) and a market with buyers and no maker draws a trial newcomer (entry_trial.py). With the year's arrays
    (year_arrays.py) every cost the rules read, and the tile a newcomer is sited on, come from tables over them
    (entry_tables.py); without, from the records."""
    money = setup.currency_id
    started = 0
    by_limits = sites.limits_by_recipe(setup.site_limits)
    plans = year_plans(setup, record, view, area_map, unmet_by_market, carriage, bids_by_market, arrays)
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
        elif record.credit.expansion_runs.get(producer_id, 0.0) > 0.0:     # a working-capital loan builds no plant
            continue                                    # plant it already asked for is still to come
        if not builds_plant:
            producer = replaced(producer, capacity_runs=producer.capacity_runs + plan.runs,
                                workshops=producer.workshops + 1)
        producer_table.put_producer(record.producers, producer)
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
                record.credit.ask_for_loan(LoanRequest(producer_id, money, loan, credit.earnable_rate(plan.yearly_return),
                                                       recipe.plant_life_years, loan, "enter"))
                record.credit.plan_expansion(producer_id, loan / per_run)
    return started


def _spare_at(grid, costs, good: str, area_id: str) -> float:
    """The spare output of the grid `EntryTables.spare_output` makes, for one good and area (nothing for a pair it does not hold)."""
    good_column = costs.goods.row.get(good)
    area_column = costs.arrays.area_index.areas.row.get(area_id)
    return 0.0 if good_column is None or area_column is None else float(grid[good_column, area_column])


def _carriage(setup):
    return setup.carriage_table()


def _traded_volume(record, view, area_map):
    """What a good's market (on a tile) carried last year; None for a good with no market."""
    goods = set(area_map.goods())

    def traded(good, tile):
        return record.goods.volumes.get(market_key(good, view.area_of(good, tile)), 0.0) if good in goods else None
    return traded


def restake_owners(setup, record, view) -> None:
    """Owners put working cash back into producers whose runs pay but that ran out of it."""
    money = setup.currency_id
    rate = own_rate(view, money)
    # an owner risks at most the stake share of its cash a year, across all the producers it owns
    budget = {}
    for producer_id, producer in sorted(record.producers.items()):
        if producer.capacity_runs <= 0.0:
            continue
        shortfall = producer.cash_target - record.book.balance(producer_id, money)
        if shortfall <= 0.0:
            continue
        recipe = setup.recipes[producer.recipe_id]
        earning = unit_cost.return_after_recovery(recipe, expected_output_prices(producer, recipe, view) or {},
                                                  live_input_prices(producer, recipe, view),
                                                  live_wages(producer, recipe, view), rate,
                                                  producer.land_rent_per_run)
        pays = earning is not None and earning > rate
        if producer.owner not in budget:
            budget[producer.owner] = ENTRANT_OWNER_STAKE_SHARE * max(0.0, record.book.balance(producer.owner, money))
        amount = min(restake(shortfall, record.book.balance(producer.owner, money), pays), budget[producer.owner])
        if amount > 0.0:
            budget[producer.owner] -= amount
            record.book.transfer(Transfer(producer.owner, producer_id, money, amount, "owner's stake"))


def close_idle_producers(setup, record) -> int:
    """Close producers with nothing left to do (entry.producers_to_close) by the one exit (producer_exit.exit_producer): their
    cash is paid out as a dividend, shared with the holders of their shares and spread over their owner's tile, and any goods
    they still hold go to their owner."""
    money = setup.currency_id
    debtors = {loan.borrower for loan in record.credit.loans}
    closing = producers_to_close(record.producers, set(record.credit.expansion_runs), debtors)
    for producer_id in closing:
        cash = record.book.balance(producer_id, money)
        payout = [Transfer(producer_id, record.producers[producer_id].owner, money, cash, "dividend")] if cash > 0.0 else []
        producer_exit.exit_producer(record, producer_id, payout)
    return len(closing)


def _spare_output(setup, record, view) -> Dict[Tuple[str, str], float]:
    """Output (good, area) the market's makers could have added from idle capacity last year."""
    spare: Dict[Tuple[str, str], float] = {}
    for producer in sites.in_id_order(record.producers):
        recipe = setup.recipes[producer.recipe_id]
        # capacity waiting on a plant loan counts too, so one gap does not bring a newcomer every year
        idle = idle_runs(producer.capacity_runs, producer.last_runs, record.credit.expansion_runs.get(producer.agent_id, 0.0),
                         producer.land_run_cap)
        if idle <= 0.0:
            continue
        for good, made in recipe.outputs.items():
            key = (good, view.area_of(good, producer.tile))
            spare[key] = spare.get(key, 0.0) + idle * made * producer.yield_factor
    return spare
