"""The year's entry: the markets with unmet demand become new producers (entry.py), each owned by the
richest household of its tile (newcomers to a recipe already worked on the tile join that producer's
capacity), which stakes part of its cash as working cash; one with plant to build
asks the credit market for it, and its capacity grows as the plant goods arrive. Owners also put working
cash back into paying producers that ran out of it."""
import math
from typing import Dict, List, Tuple

import numpy as np

from sim.book_apply import RULE_SINGLE

from . import producer_table
from .posting_sequence import post_in_order
from . import (credit, entry_kernels, entry_margin_tables, entry_plan_table, entry_practice, entry_unmet, location, ownership, practice, producer_exit, sites,
               unit_cost, year_bids)
from .entry_backed import unfilled_at_cost
from .entry_bid_markets import makers_of, weigh
from .entry_margin import margin_entry_plans
from .entry_spare import idle_runs
from .entrant_rent import site_rent_per_run
from .entry_tables import EntryTables
from .entry_trial import reachable_capacity, trial_entry_plans
from .entry import (ENTRANT_OWNER_STAKE_SHARE, EntryPlan, UnmetDemand, entrant_loan, entry_plans, gap_beyond_spare,
                    producers_to_close, restake)
from .producers import Producer, expected_output_prices, live_input_prices, live_wages
from .producers_close import working_capital_target
from .market_memory import market_key
from .setup import recipe_tile_key
from .types import LoanRequest, Transfer
from .year_arrays_costs import refreshed
from .replaced import replaced
from .rates import own_rate


def year_plans(setup, record, view, area_map, unmet_by_market: Dict[Tuple[str, str], float], carriage=None,
               bids_by_market=None, arrays=None) -> List[EntryPlan]:
    """The year's entry plans, in the order they are applied: the unmet markets' (entry.py), then the margin's and the trial's
    where there are bids. See `open_entrants` for `arrays`. With the arrays the plans are those of `year_plan_table`, as objects."""
    if arrays is not None:
        costs, table = year_plan_table(setup, record, view, area_map, unmet_by_market, carriage, bids_by_market, arrays)
        return entry_plan_table.as_plans(table, costs)
    with entry_practice.shared_crews(record.producers):
        spare = _spare_output(setup, record, view)
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
            gap = gap_beyond_spare(quantity, spare.get((good, area_id), 0.0))
            if gap > 0.0:
                unmet[(good, area_id)] = UnmetDemand(good, area_id, area.anchor_tile, gap)
        siting = location.entry_siting(setup, record, view, area_map, carriage or _carriage(setup), None)
        traded = _traded_volume(record, view, area_map)
        block = year_bids.of(bids_by_market) if bids_by_market else None
        plans = entry_plans(setup.recipes, view, unmet, traded, siting,
                            unfilled_at_cost(setup, record, view, area_map, block, traded, None),
                            lambda recipe_id, tile: site_rent_per_run(setup, record, view, recipe_id, tile),
                            entry_practice.crews_of_recipe(record.producers), None)
        if block is not None:
            planned = tuple((plan.good, view.area_of(plan.good, plan.tile)) for plan in plans)
            first_margin_plan = len(plans)
            weighed = weigh(block, makers_of(setup.recipes), area_map, view, reachable_capacity(record, setup, None))
            plans += margin_entry_plans(setup, record, view, area_map, block, planned, siting, None, weighed)
            planned += tuple((plan.good, view.area_of(plan.good, plan.tile)) for plan in plans[first_margin_plan:])
            plans += trial_entry_plans(setup, record, view, area_map, block, planned, siting, None, weighed)
    return plans


def year_plan_table(setup, record, view, area_map, unmet_by_market: Dict[Tuple[str, str], float], carriage, bids_by_market, arrays):
    """(the year's entry tables, the plans as an `EntryPlans` table): the unmet markets' plans come out of one kernel
    (`entry_unmet.unmet_plan_table`), the margin's and the trial's follow where there are bids."""
    with entry_practice.shared_crews(record.producers):
        costs = EntryTables.build(setup, record, view, area_map, arrays.sync(setup, record, view), carriage or _carriage(setup),
                                  entry_practice.crews_of_recipe(record.producers))
        block = year_bids.of(bids_by_market) if bids_by_market else None
        plans = entry_unmet.unmet_plan_table(costs, block, unmet_by_market)
        if block is not None:
            weighed = entry_margin_tables.Weighed(costs, block)
            skipped = entry_margin_tables.skipped_cells(costs, plans)
            margin = entry_margin_tables.margin_plan_table(costs, record, block, weighed, skipped)
            skipped |= entry_margin_tables.skipped_cells(costs, margin)
            trial = entry_margin_tables.trial_plan_table(costs, block, weighed, skipped)
            plans = entry_plan_table.joined(entry_plan_table.joined(plans, margin), trial)
    return costs, plans


def _plans_to_apply(setup, record, view, area_map, unmet_by_market, carriage, bids_by_market, arrays):
    """The year's plans as (recipe id, tile, runs, yearly return), in the order they are applied: the columns of the plan table with the
    year arrays, else the plan objects."""
    if arrays is None:
        return [(plan.recipe_id, plan.tile, plan.runs, plan.yearly_return) for plan in year_plans(
            setup, record, view, area_map, unmet_by_market, carriage, bids_by_market, None)]
    costs, table = year_plan_table(setup, record, view, area_map, unmet_by_market, carriage, bids_by_market, arrays)
    used = entry_plan_table.count(table)
    recipe_ids, tile_ids = costs.matrices.recipes.ids, costs.tiles.ids
    return list(zip(map(recipe_ids.__getitem__, table.recipe_row[:used].tolist()), map(tile_ids.__getitem__, table.tile_row[:used].tolist()),
                    table.runs[:used].tolist(), table.yearly_return[:used].tolist()))


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
    plans = _plans_to_apply(setup, record, view, area_map, unmet_by_market, carriage, bids_by_market, arrays)
    peers_of_recipe: Dict[str, list] = {}       # each recipe's producers' crews, a newcomer's included once it starts
    owner_cash: Dict[str, float] = {}           # each owner's cash as the stakes already decided leave it
    stakes: List[Transfer] = []          # the stakes, posted together after the plans are applied, one batch each
    if plans:
        for each in record.producers.values():
            peers_of_recipe.setdefault(each.recipe_id, []).append(each.crew_runs)
    for plan_recipe_id, plan_tile, plan_runs, plan_return in plans:
        recipe = setup.recipes[plan_recipe_id]
        key = recipe_tile_key(plan_recipe_id, plan_tile)
        producer_id = "producer:" + key
        builds_plant = recipe.plant_life_years > 0.0 and bool(recipe.plant_goods)
        # each producer stands for the tile's workshops of one recipe: newcomers join its capacity and its workshop count
        producer = record.producers.get(producer_id)
        plan_is_new = producer is None
        if producer is None:
            owner = ownership.owner_cohort(record, plan_tile)
            if owner is None:
                continue
            producer = Producer(agent_id=producer_id, owner=owner, recipe_id=plan_recipe_id, tile=plan_tile,
                                capacity_runs=0.0, expected_sales=plan_runs,
                                crew_runs=practice.entrant_crew_runs(recipe, peers_of_recipe.get(plan_recipe_id, ())),
                                yield_factor=sites.yield_at(recipe, plan_tile, by_limits,
                                                            setup.yield_factor_by_recipe_tile.get(key, 1.0)))
        elif record.credit.expansion_runs.get(producer_id, 0.0) > 0.0:     # a working-capital loan builds no plant
            continue                                    # plant it already asked for is still to come
        if not builds_plant:
            producer = replaced(producer, capacity_runs=producer.capacity_runs + plan_runs,
                                workshops=producer.workshops + 1)
        if plan_is_new:
            peers_of_recipe.setdefault(plan_recipe_id, []).append(producer.crew_runs)
        producer_table.put_producer(record.producers, producer)
        started += 1
        inputs, wages = live_input_prices(producer, recipe, view), live_wages(producer, recipe, view)
        if producer.owner not in owner_cash:
            owner_cash[producer.owner] = record.book.balance(producer.owner, money)
        stake = min(working_capital_target(practice.recipe_for(recipe, producer.crew_runs), plan_runs, inputs, wages),
                    ENTRANT_OWNER_STAKE_SHARE * max(0.0, owner_cash[producer.owner]))
        if stake > 0.0:
            owner_cash[producer.owner] -= stake
            stakes.append(Transfer(producer.owner, producer_id, money, stake, "stake in a new workshop"))
        if builds_plant:
            per_run = unit_cost.plant_value_per_run(recipe, inputs, wages)
            loan = entrant_loan(per_run * plan_runs, stake) if per_run > 0.0 and math.isfinite(per_run) else 0.0
            if loan > 0.0:
                record.credit.ask_for_loan(LoanRequest(producer_id, money, loan, credit.earnable_rate(plan_return),
                                                       recipe.plant_life_years, loan, "enter"))
                record.credit.plan_expansion(producer_id, loan / per_run)
    post_in_order(record.book, [([stake], ()) for stake in stakes], RULE_SINGLE)
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


def restake_owners(setup, record, view, arrays=None) -> None:
    """Owners put working cash back into producers whose runs pay but that ran out of it. Over the year `arrays` the stakes are
    worked out in one kernel (`entry_kernels.restake_amounts`); without them, producer by producer."""
    money = setup.currency_id
    rate = own_rate(view, money)
    if arrays is not None and _restake_over_arrays(setup, record, view, arrays, money, rate):
        return
    # an owner risks at most the stake share of its cash a year, across all the producers it owns
    budget = {}
    reads: Dict[Tuple[str, str], tuple] = {}      # (recipe, tile) -> the live input prices and wages every producer there reads
    for producer_id, producer in sorted(record.producers.items()):
        if producer.capacity_runs <= 0.0:
            continue
        shortfall = producer.cash_target - record.book.balance(producer_id, money)
        if shortfall <= 0.0:
            continue
        recipe = setup.recipes[producer.recipe_id]
        key = (producer.recipe_id, producer.tile)
        if key not in reads:
            reads[key] = (live_input_prices(producer, recipe, view), live_wages(producer, recipe, view))
        inputs, wages = reads[key]
        earning = unit_cost.return_after_recovery(recipe, expected_output_prices(producer, recipe, view) or {}, inputs, wages, rate,
                                                  producer.land_rent_per_run)
        pays = earning is not None and earning > rate
        if producer.owner not in budget:
            budget[producer.owner] = ENTRANT_OWNER_STAKE_SHARE * max(0.0, record.book.balance(producer.owner, money))
        amount = min(restake(shortfall, record.book.balance(producer.owner, money), pays), budget[producer.owner])
        if amount > 0.0:
            budget[producer.owner] -= amount
            record.book.transfer(Transfer(producer.owner, producer_id, money, amount, "owner's stake"))


def _restake_over_arrays(setup, record, view, arrays, money: str, rate: float) -> bool:
    """`restake_owners` over the arrays brought in step with the records and the memory now. False (nothing done) where an owner is
    itself a producer, whose cash a stake would change before its own turn."""
    arrays = refreshed(arrays, setup, record, view)
    columns, matrices, memory = arrays.producers, arrays.matrices, arrays.memory
    balance = record.book.balance
    ids = columns.ids
    cash = record.book.balances_at(record.book.rows_of(ids), money)
    shortfall = np.where(columns.capacity_runs > 0.0, columns.cash_target - cash, 0.0)
    wanting = np.nonzero(shortfall > 0.0)[0]
    owners = sorted({columns.records[row].owner for row in wanting})
    if any(owner in record.producers for owner in owners):
        return False
    owner_row = {owner: position for position, owner in enumerate(owners)}
    owner_of = np.zeros(len(ids), dtype=np.int64)
    for row in wanting:
        owner_of[row] = owner_row[columns.records[row].owner]
    owner_cash = np.array([balance(owner, money) for owner in owners], dtype=np.float64)
    amounts = entry_kernels.restake_amounts(
        columns.recipe_row, columns.tile_row, shortfall, columns.land_rent_per_run, columns.expected_prices, owner_of, owner_cash,
        matrices.slot_goods, matrices.inputs, matrices.outputs, matrices.plant_goods, matrices.labour_hours,
        matrices.plant_labour_hours, matrices.plant_life_years, memory.price, memory.offered, memory.wage,
        arrays.area_index.of_good_tile, float(rate), ENTRANT_OWNER_STAKE_SHARE)
    post_in_order(record.book, [([Transfer(columns.records[row].owner, ids[row], money, float(amounts[row]), "owner's stake")], ())
                                for row in np.nonzero(amounts > 0.0)[0]], RULE_SINGLE)
    return True


def close_idle_producers(setup, record) -> int:
    """Close producers with nothing left to do (entry.producers_to_close) by the one exit (producer_exit.exit_producer): their
    cash is paid out as a dividend, shared with the holders of their shares and spread over their owner's tile, and any goods
    they still hold go to their owner."""
    money = setup.currency_id
    store = record.credit.contracts.loan_store
    debtors = {store.agent_name(number) for number in np.unique(store.table.borrower[:len(store)]).tolist()}
    closing = producers_to_close(record.producers, set(record.credit.expansion_runs), debtors)
    exits = producer_exit.ExitBatch(record)
    for producer_id in closing:
        cash = record.book.balance(producer_id, money)
        payout = [Transfer(producer_id, record.producers[producer_id].owner, money, cash, "dividend")] if cash > 0.0 else []
        exits.exit(producer_id, payout)
    exits.finish()
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
