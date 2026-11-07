"""The economy at the opening: who exists, what they hold, and how much each producer can make.

Initial conditions only. People per tile come from the engine; the opening prices and wages seed
expectations. Producers' capacity is sized so the opening supplies what households demand at those
prices, through the recipes the society already runs (input-output: final demand plus what the
producers of it consume, back to raw materials). Each agent's opening cash is what it wants to hold,
struck at the mint: the money stock is derived, not authored. After this the markets take over.
"""
import dataclasses
import math
from typing import Dict, List, Tuple

from sim.constants import declare
from sim.labour.api import MarketState
from sim.refusal import Refusal

from . import producer_table
from .home_scope import has_partners
from . import households_cohort
from . import recipes as recipes_module
from . import carriage_fleet_book, durable_stock, equity, land_lease_year, goods_market, opening_basket, opening_bid_memory, opening_demand, opening_income, opening_metal, opening_own, opening_placement, opening_plans, opening_rent, opening_resting, opening_runs, opening_runs_pack, households, households_store, labour_state, location, location_inputs, mint, opening_stores, ownership, sites, titles
from sim.book import Book
from .market_areas import AreaMap
from .market_memory import MarketMemory, YearView, market_key
from . import merchants
from .merchants import Merchant
from .producers import Producer, paying_output
from .producers_close import working_capital_target
from .replaced import replaced
from .carriage_record import CarriageRecord
from .record import EconomyRecord
from .setup import EconomySetup, labour_area, recipe_tile_key
from .tile_costs import CarriageTable
from .types import EDGE_MINT, EDGE_PRODUCTION, GoodId, GoodsMove, Recipe, TileId, Transfer

MERCHANTS_PER_TILE = declare(
    "MERCHANTS_PER_TILE", 0.1, kind="temporary_heuristic",
    unit="merchant agents per tile held", source=None, confidence="D",
    why="Enough independent merchant houses that several chase one price gap and compete, few enough "
        "to stay cheap to simulate. Each agent stands for many traders; the count is not a headcount.")
MERCHANT_CAPITAL_SHARE_OF_OUTPUT = declare(
    "MERCHANT_CAPITAL_SHARE_OF_OUTPUT", 0.02, kind="temporary_heuristic",
    unit="share of the opening's yearly output value", source=None, confidence="D",
    why="The merchant class's working capital against what the economy makes in a year. Not measured "
        "for any civilisation here; the engine's merchant class capital (merchant_terms) is a "
        "different estimate of the same thing.")


# numerical bounds on raising the opening prices to the rent they must pay (opening_rent.py)
COVERING_PRICE_PASSES = 4
COVERING_PRICE_TOLERANCE = 1e-3

# numerical bounds on settling the share of hours producers hire against the demand it implies (opening_own.py)
OWN_PLOT_PASSES = 8
OWN_PLOT_TOLERANCE = 1e-4


class OpeningIncomeRefused(ValueError):
    """The opening has no income at which its households save nothing; `refusal` says why (its `cause` and `facts`)."""
    def __init__(self, refusal: Refusal):
        super().__init__(str(refusal))
        self.refusal = refusal


def open_economy(setup: EconomySetup) -> Tuple[EconomyRecord, AreaMap, CarriageTable]:
    """The opening at prices that pay the land's rent (`_with_covering_prices`)."""
    return _with_covering_prices(setup)


def _solve_opening(setup: EconomySetup, start: opening_income.OpeningStart):
    """(the opening, the service price by tile its households found) solved to a fixed point with its households' first-year choices. A first solve leaves a money stock,
    whose yearly loss of its metal is the demand (the mint's) the later solves size the producers of the backing good
    to, along with everyone else's. Each solve is read by the households (what they hire, which grains they buy
    milled, at its prices and wages) and solved again with those plans in final demand, until they stop changing
    (opening_plans.py): the producers of what the households then buy are sized to it, and labour to the household
    work they hire, as far as the hands left by the other producers go (past that the service price rises). Each opening
    starts its income and hired share from what the one before found (`start`)."""
    first = _open(setup, 0.0, start=start)
    replacement = opening_metal.yearly_replacement(setup, first[0])
    cache: Dict[str, Tuple[EconomyRecord, AreaMap, CarriageTable]] = {
        "bare": first if replacement <= 0.0 else _open(setup, replacement, start=start)}
    first = None        # no longer needed when the money loses metal: the solve holds the bare opening, not both

    def open_with(plans):
        if plans is None:
            return cache["bare"]
        return _open(setup, replacement, plans, start)

    def choose(opened):
        if "room" not in cache:
            bare = open_with(None)[0]
            per_hour = _servant_hours_per_hired_hour(setup)
            cache["room"] = {tile: hands / per_hour if per_hour > 0.0 else math.inf
                             for tile, hands in opening_plans.hands_left_by_tile(setup, bare).items()}
        return opening_plans.household_plans(setup, opened[0], opened[1], cache["room"])
    settled = opening_plans.settle(open_with, choose, lambda opened: opened[0].cohorts)
    floors = choose(settled).service_price_by_tile
    opening_plans.post_service_prices(settled[0].memory, settled[1], setup, floors)
    return settled, floors


def _with_covering_prices(setup):
    """The opening at prices that pay the land's rent as well as the costs. The rent a tile's land fetches depends on what
    its producers sell and what households' plots take, so the prices are raised from the rent shares the last opening
    left until they stop moving (opening_rent.py); a setup whose recipes pay no rent is solved once. Only the first
    pass is the full solve (`_solve_opening`): the households' plans it settled (who hires, which grains are bought
    milled) are kept for the later passes, which open the economy at the covered prices with those plans (`_reopen`)."""
    start = opening_income.OpeningStart()
    settled, floors = _solve_opening(setup, start)
    plans = opening_plans.HouseholdPlans(
        {agent_id: (cohort.hired_work_per_person, 0.0, cohort.milled_grains) for agent_id, cohort in settled[0].cohorts.items()},
        floors)
    current = setup
    for _pass in range(COVERING_PRICE_PASSES):
        record = settled[0]
        covered = opening_rent.covering_prices(
            setup.recipes, setup.opening_prices, setup.opening_wages, opening_rent.shares_of_revenue(current, record),
            {producer.recipe_id for producer in record.producers.values()}, opening_runs.mean_yields(setup, setup.recipes))
        if all(good in current.opening_prices
               and abs(price - current.opening_prices[good]) <= COVERING_PRICE_TOLERANCE * price      # an unpriced good has not settled
               for good, price in covered.items()):
            break
        current = dataclasses.replace(setup, opening_prices=covered)
        record = None
        settled = None      # the opening at the old prices is not read again: not held while the next one is built
        settled = _reopen(current, plans, start)
    return settled


def _reopen(setup, plans, start):
    """The opening at `setup`'s prices with the households holding `plans` (no new settling of them): the metal the
    money loses is sized from a first opening at these prices, as in `_solve_opening`, and the service price the plans found
    is posted again."""
    replacement = opening_metal.yearly_replacement(setup, _open(setup, 0.0, start=start)[0])
    settled = _open(setup, replacement, plans, start)
    opening_plans.post_service_prices(settled[0].memory, settled[1], setup, plans.service_price_by_tile)
    return settled


def _servant_hours_per_hired_hour(setup: EconomySetup) -> float:
    """Hours of labour a year the producers of an hour of household work hire per hour hired: what a unit of the
    service takes (the dearest way, where several make it)."""
    return max([math.fsum(recipe.labour_hours.values()) / made
                for good in opening_plans.service_goods(setup, setup.capital_tile)
                for recipe in setup.recipes.values() for made in [recipe.outputs.get(good, 0.0)] if made > 0.0] or [0.0])


def _open(setup: EconomySetup, replacement: float, plans=None, start=None) -> Tuple[EconomyRecord, AreaMap, CarriageTable]:
    carriage = setup.carriage_table()
    priced_goods = {good: price for good, price in setup.opening_prices.items()
                    if good in setup.specs and price > 0.0}
    area_map = setup.area_map(carriage)
    memory = _opening_memory(setup, area_map, priced_goods)
    record = EconomyRecord(book=Book(), memory=memory, currency=setup.currency,
                           carriage=CarriageRecord(ways={key: dict(built) for key, built in setup.improvements.items()}))
    view = YearView(memory, record.book, area_map, setup.currency_id, setup, labour_area)
    _open_cohorts(setup, record)
    if plans is not None:
        households_cohort.put_cohorts(record.cohorts, opening_plans.with_plans(record.cohorts, plans))
    own = opening_own.OwnPlots(setup, record)
    start = opening_income.OpeningStart() if start is None else start
    own.share_hired = start.share_hired or 0.0
    packed = _settle_income(setup, record, view, priced_goods, replacement, own, start)
    start.share_hired = own.share_hired
    # the demand after the settle is asked of the packed cohorts, who hold the stock they held when the income was settled
    # (the old path reads the orders of the last ask again at the same income); only a settle that did not end at the
    # incomes the cohorts hold asks the old path, with the orders of the last ask left for it
    after_settle = packed if packed is not None and packed.asked_at_incomes_now(record) else None
    if packed is not None and after_settle is None:
        packed.remember_orders(record)
    _seed_durable_stocks(setup, record, view, packed)
    final_by_tile = (_final_demand_packed(setup, record, replacement, after_settle) if after_settle is not None
                     else _final_demand(setup, record, view, replacement, own=own))
    for country in setup.countries():
        _open_country_producers(setup, record, area_map, carriage, priced_goods, final_by_tile, country)
    sites.apply_site_limits(record, setup)
    opening_runs.fit_to_supply(setup, record)
    rent = opening_rent.settle(setup, record, view, own.hectares_by_tile(record.cohorts),
                               land_lease_year.own_plot_returns(setup, record, view, own.options))
    figure = record.capital_markets.property_income
    record.capital_markets.set_property_income(opening_rent.property_income_with_rent(figure, rent))
    incomes = opening_rent.income_after_rent({agent_id: cohort.last_year_income for agent_id, cohort in record.cohorts.items()},
                                             figure, record.capital_markets.property_income)
    for agent_id, income in incomes.items():
        households_cohort.change_cohort(record.cohorts, agent_id, last_year_income=income)
    record.goods.set_index_base_prices(dict(priced_goods))
    _stock_producers_with_inputs(setup, record)
    _open_merchants(setup, record, priced_goods, final_by_tile)
    carriage_fleet_book.endow(setup, record, carriage, priced_goods, final_by_tile)
    _strike_opening_cash(setup, record, view, own.extra)
    sold_per_worker = opening_own.sold_hours_per_worker(
        own.sold_total(), math.fsum(cohort.working_people for cohort in record.cohorts.values()), setup.working_hours_per_year)
    sold_by_area = opening_placement.sold_hours_per_worker_by_area(
        own.sold, {agent_id: (labour_area(cohort.tile), cohort.working_people) for agent_id, cohort in record.cohorts.items()},
        sold_per_worker)
    record.labour.seed_sold_hours(sold_per_worker, sold_by_area)
    record.labour.seed_workforce(labour_state.opening_workforce(      # the mint's capacity follows the money struck
        setup, record, sold_by_area))
    record.labour.seed_hired_hours(opening_resting.resting_hours_held(
        opening_placement.capped_contracts(labour_state.producers_hours_by_employer(setup, record),
                                           {area: labour_state.people_by_trade(record.labour.workforce, area) for area in record.labour.workforce.workers},
                                           sold_by_area, sold_per_worker),
        setup.opening_wages))
    mint.seed_opening_metal(setup, record)
    opening_stores.seed_opening_stores(setup, record, _store_goods(setup, view, area_map, priced_goods))
    record.goods.seed_opening_demand(opening_runs.national_totals(final_by_tile), {
        country: opening_runs.national_totals({tile: final_by_tile[tile] for tile in setup.tiles_of(country) if tile in final_by_tile})
        for country in setup.countries()})
    record.goods.seed_opening_basket(opening_basket.supplied_part(setup, record, record.goods.opening_demand))
    return record, area_map, carriage


def _open_country_producers(setup, record, area_map, carriage, priced_goods, final_by_tile, country) -> None:
    """One country's producers: its own people's demand met through the recipes its techniques allow, placed
    on its own tiles. With one country and every recipe allowed everywhere this is the whole economy's opening."""
    tiles = set(setup.tiles_of(country))
    recipes = {recipe_id: recipe for recipe_id, recipe in setup.recipes.items()
               if not setup.recipes_by_country or recipe_id in setup.recipes_by_country.get(country, ())}
    final = {tile: demand for tile, demand in final_by_tile.items() if tile in tiles}
    ceilings = opening_runs.run_ceilings(recipes, sites.limits_by_recipe(setup.site_limits))
    yields = opening_runs.mean_yields(setup, recipes, tiles)
    ranked, runs = opening_runs.choose_recipes(final, recipes, priced_goods, setup.opening_wages, setup.opening_rate,
                                               ceilings, yields)
    incumbents = opening_runs.first_choices(ranked)
    _place_producers(setup, record, area_map, carriage, final, incumbents, runs, yields,
                     tiles if has_partners(setup) else None)


def _store_goods(setup, view, area_map, priced_goods) -> set:
    """The goods fit to hold as wealth at the opening prices, as households choose them."""
    tile = setup.capital_tile
    staple = households_store.staple_price_per_kg(households.need_prices(setup.basket_for(tile), view, tile), setup.specs)
    quoted = {good: view.price(good, area_map.area_of(good, tile)) for good in priced_goods}
    prices = {good: price for good, price in quoted.items() if price is not None}    # a good with no price is not a candidate
    return set(households_store.store_candidates(setup.specs, prices, staple, money_level=1.0))   # the opening's money is opening-year money


def _opening_memory(setup, area_map, priced_goods) -> MarketMemory:
    memory = MarketMemory(year=0, rates={setup.currency_id: setup.opening_rate},
                          basket_price_levels={setup.currency_id: 1.0}, last_year_prices=dict(priced_goods))
    for good, price in priced_goods.items():
        for area in area_map.areas(good):
            memory.set_price(market_key(good, area.area_id), price)
            memory.note_usual_price(market_key(good, area.area_id))
    # the seeds equal the opening wages at level one, the figure trade_wages gives an unhired trade in the first year; the first close rebuilds the memory's wages from clearings
    seeds = MarketState(wages={labour_area(tile): dict(setup.opening_wages) for tile in setup.tiles})
    labour_state.mirror_wages(memory.wages, seeds)       # the mirror is the one writer of the remembered wages
    return memory


def _full_employment_income_per_head(setup) -> float:
    return setup.opening_wages[setup.unskilled_trade] * setup.working_hours_per_year * setup.working_share


def _open_cohorts(setup, record) -> None:
    income = _full_employment_income_per_head(setup)
    for tile, people in sorted(setup.opening_population_by_tile.items()):
        for cohort in households.cohorts_for_tile(tile, people, setup.working_share, setup.gini,
                                                  opening_income_per_capita=income):
            households_cohort.put_cohort(record.cohorts, cohort)
    titles.seed(record)


def _settle_income(setup, record, view, priced_goods, replacement, own, start) -> None:
    """Households' opening income is the value of the final demand it pays for, not the full-employment ceiling
    (opening_income.py): the producers sized to that demand then pay out the income the households received.
    Workers are paid alike out of the labour share of it; owners receive the rest by what they own. The demand is what
    households buy after their own plots (opening_own.py), whose hours depend on the runs that demand takes: at each
    income the share of hours producers hire is settled first, always from the share this solve began with (a nearby
    income's share is nearly its own), so the demand is a function of the income alone. `start` carries the last income found and share hired into the next opening."""
    people = math.fsum(cohort.people for cohort in record.cohorts.values())
    recipes = setup.recipes
    ceilings = opening_runs.run_ceilings(recipes, sites.limits_by_recipe(setup.site_limits))
    yields = opening_runs.mean_yields(setup, recipes)
    ranked = opening_runs.ranked_recipes(recipes, priced_goods, setup.opening_wages, setup.opening_rate, None, yields)
    main = opening_runs.main_outputs(recipes, priced_goods)
    share = {"labour": 0.0}
    memory = opening_bid_memory.BidMemory()
    hands_hours = math.fsum(cohort.working_people for cohort in record.cohorts.values()) * setup.working_hours_per_year
    warm_share = own.share_hired
    packed = opening_demand.OpeningDemand.of_settlement(setup, record, view, memory, own, replacement)
    fast = packed if packed.supported else None     # a settlement the kernel does not cover is asked the old way
    solver = opening_runs_pack.RunSolver(recipes, ranked, ceilings, yields, main, setup.opening_wages) if fast else None

    def demand_at(per_head):
        own.share_hired = warm_share
        households_cohort.put_cohorts(record.cohorts, opening_income.with_income(record.cohorts, per_head, share["labour"]))
        if fast:
            value, needed, bill = fast.ask(record, solver, priced_goods, hands_hours, OWN_PLOT_PASSES, OWN_PLOT_TOLERANCE)
            producible = value * opening_income.producible_share_of_hours(needed, own.sold_total())
            share["labour"] = opening_income.labour_share_of_bill(bill, value + own.in_kind)
            return producible + own.in_kind, share["labour"]
        for _pass in range(OWN_PLOT_PASSES):
            own.in_kind = 0.0
            final = _final_demand(setup, record, view, replacement, memory, own)
            runs = opening_runs.required_runs(final, ranked, recipes, ceilings, yields, main)
            if own.note_runs(runs, hands_hours) <= OWN_PLOT_TOLERANCE:
                break
        # only what the working hands can make is income that producers pay out (Complaint 607)
        value = opening_income.value_of(final, priced_goods)
        producible = value * opening_income.producible_share(runs, recipes, own.sold_total())
        share["labour"] = opening_income.labour_share_of(runs, recipes, setup.opening_wages, value + own.in_kind)
        return producible + own.in_kind, share["labour"]     # what they grow is spending in kind: not saved, not bought

    ceiling = _full_employment_income_per_head(setup)
    settled = opening_income.settled_income_per_head(ceiling, people, demand_at, start.income_per_head)
    if isinstance(settled, Refusal):
        raise OpeningIncomeRefused(settled)
    per_head, labour_share = settled
    if per_head < ceiling:      # a ceiling income says nothing about where the next root lies
        start.income_per_head = per_head
    share["labour"] = labour_share
    demand_at(per_head)     # leaves the plots at the settled income's share of hours hired
    households_cohort.put_cohorts(record.cohorts, opening_income.with_income(record.cohorts, per_head, labour_share))
    record.capital_markets.set_property_income(opening_income.property_income_of(record.cohorts, per_head, labour_share))
    return fast


def _opening_bids(setup, record, view, memory=None, stationary_durables=True, own=None):
    """(cohort, bid, price) for what each cohort would buy at the opening prices with the opening income. A `memory`
    (opening_bid_memory.py) kept across calls that change only incomes spares the work that does not depend on them."""
    memory = opening_bid_memory.BidMemory() if memory is None else memory
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        basket = memory.basket(setup, record, cohort)
        priced = memory.priced(setup, record, view, cohort, basket)
        income = cohort.last_year_income
        def make(cash=income):
            return households.goods_orders(cohort, view, cash, income, basket, setup.specs,
                                           priced, shared_store=memory.stores(record, cohort),
                                           stationary_durables=stationary_durables)
        orders = make() if own is None else own.resting_orders(record, cohort, income, basket, priced, make)
        for bid in orders.bids:
            price = view.price(bid.good, bid.area)
            if price:
                yield cohort, bid, price


def _seed_durable_stocks(setup, record, view, packed=None) -> None:
    """Households open at the planning date, holding their serving stock after year-end losses.
    Their first purchases replace those losses, as in a later year with the same desired flow. `packed` (the settled
    cohorts, when the settle packed them) gives the bids of the durables that serve needs."""
    if packed is not None:
        bids = [(cohort, good, quantity) for cohort, good, quantity in packed.durable_bids(record)]
    else:
        bids = [(cohort, bid.good, bid.floor_quantity + bid.flexible_quantity)
                for cohort, bid, _price in _opening_bids(setup, record, view, stationary_durables=False)
                if bid.priority != households_store.STORE_PRIORITY]     # a store of wealth is seeded from the deposits (opening_stores), not from need
    moves = []
    for cohort, good, wanted in bids:
        spec = setup.specs.get(good)
        if spec is None or spec.service_life_years <= 0.0:
            continue
        quantity = durable_stock.after_year_end_losses(wanted, spec)
        if quantity > 0.0:
            moves.append(GoodsMove(EDGE_PRODUCTION, cohort.agent_id, good, cohort.tile, quantity,
                                   "opening stock of a durable in use"))
    if moves:
        record.book.move_many(moves)


def _final_demand(setup, record, view, replacement=0.0, memory=None, own=None) -> Dict[TileId, Dict[GoodId, float]]:
    """What each tile's households buy at the opening prices with the opening income, and the metal the mint
    buys to replace what the money loses (at the capital)."""
    final: Dict[TileId, Dict[GoodId, float]] = {}
    for cohort, bid, price in _opening_bids(setup, record, view, memory, own=own):
        demand = final.setdefault(cohort.tile, {})
        demand[bid.good] = demand.get(bid.good, 0.0) + goods_market.quantity_at(bid, price)
    if replacement > 0.0:
        demand = final.setdefault(setup.capital_tile, {})
        metal = record.currency.backing_good
        demand[metal] = demand.get(metal, 0.0) + replacement
    return final


def _final_demand_packed(setup, record, replacement, packed) -> Dict[TileId, Dict[GoodId, float]]:
    """`_final_demand` for the settled cohorts, asked of the arrays they were packed into."""
    final = packed.final_demand(record)
    if replacement > 0.0:
        demand = final.setdefault(setup.capital_tile, {})
        metal = record.currency.backing_good
        demand[metal] = demand.get(metal, 0.0) + replacement
    return final


def _placement_order(runs, recipes, setup) -> List[str]:
    """Recipes in the order they are placed: site-bound recipes with declared limits first (their tiles are
    fixed, so their users are sited by them), then each recipe after every recipe that uses what it makes, so
    the users of an input are on the map before its suppliers are placed beside them. A cycle falls back to id order."""
    users = {}
    for recipe_id in runs:
        recipe = recipes[recipe_id]
        for good in list(recipe.inputs) + list(recipe.plant_goods):
            users.setdefault(good, set()).add(recipe_id)
    produced = {recipe_id: paying_output(recipes[recipe_id], setup.opening_prices) for recipe_id in runs}
    by_limits = sites.limits_by_recipe(setup.site_limits)
    ordered: List[str] = [recipe_id for recipe_id in sorted(runs) if sites.is_sited(recipes[recipe_id], by_limits)]
    hands_only = [recipe_id for recipe_id in sorted(runs) if recipe_id not in ordered and _only_hands(recipes[recipe_id], setup)]
    waiting = [recipe_id for recipe_id in sorted(runs) if recipe_id not in ordered and recipe_id not in hands_only]
    while waiting:
        ready = [recipe_id for recipe_id in waiting
                 if all(user in ordered or user == recipe_id for user in users.get(produced[recipe_id], ()))]
        step = ready or waiting[:1]
        ordered.extend(step)
        waiting = [recipe_id for recipe_id in waiting if recipe_id not in step]
    return ordered + hands_only


def _only_hands(recipe: Recipe, setup) -> bool:
    """A service made from hours alone (nothing bought, no plant, flagged a service in data or with nothing to carry): it is made where it is wanted by
    whoever has hands left, so it is placed after the producers that need a place for their inputs."""
    spec = setup.specs.get(paying_output(recipe, setup.opening_prices))
    return (bool(recipe.labour_hours) and not recipe.inputs and not recipe.plant_goods
            and (recipe.service or (spec is not None and not spec.portable)))


def _within(area, tiles):
    """The part of a market area on `tiles`; None when none of it is."""
    kept = tuple(tile for tile in area.tiles if tile in tiles)
    if not kept:
        return None
    return area if len(kept) == len(area.tiles) else dataclasses.replace(
        area, tiles=kept, anchor_tile=area.anchor_tile if area.anchor_tile in kept else kept[0])


def _sited_shares(shares, limits):
    """A sited recipe's runs by area: an area holding a site keeps its share for its own sites; the areas
    holding none pool theirs on the first of them, which opening_split then spreads over every site."""
    held = [(area, runs) for area, runs in shares if any(tile in limits for tile in area.tiles)]
    bare = [(area, runs) for area, runs in shares if not any(tile in limits for tile in area.tiles)]
    return held + ([(bare[0][0], math.fsum(runs for _area, runs in bare))] if bare else [])


def _place_producers(setup, record, area_map, carriage, final_by_tile, incumbents, runs, yields, within=None) -> None:
    """Each market area of the recipe's main output gets its share of the runs, sized by the area's share
    of the demand for that good (households' and the already placed producers' that use it as an input; its
    people's share when nobody buys it), spread over its tiles by location.opening_split: one producer per
    (recipe, tile). An input is therefore opened where its users are, with the supply their capacity needs,
    not where people happen to live (a good too cheap to carry has a market the size of a tile). A processor
    of a good that only fixed sites supply is placed by location_inputs instead: beside that supply, up to it."""
    population = setup.opening_population_by_tile
    by_limits = sites.limits_by_recipe(setup.site_limits)
    input_demand: Dict[TileId, Dict[GoodId, float]] = {}
    for recipe_id in _placement_order(runs, setup.recipes, setup):
        count = runs[recipe_id]
        recipe = setup.recipes[recipe_id]
        main = paying_output(recipe, setup.opening_prices)
        areas = area_map.areas(main) if main in area_map.goods() else ()
        if within is not None:
            areas = tuple(part for part in (_within(area, within) for area in areas) if part is not None)
        if not areas:
            continue
        weights = {}
        for area in areas:
            weight = math.fsum(final_by_tile.get(tile, {}).get(main, 0.0) + input_demand.get(tile, {}).get(main, 0.0)
                               for tile in area.tiles)
            weights[area.area_id] = (area, weight)
        if math.fsum(weight for _area, weight in weights.values()) <= 0.0:
            weights = {area.area_id: (area, math.fsum(population.get(tile, 0.0) for tile in area.tiles))
                       for area in areas}
        total = math.fsum(weight for _area, weight in weights.values())
        shares = [(area, count * weight / total) for _id, (area, weight) in sorted(weights.items())
                  if total > 0.0 and weight > 0.0]
        if sites.is_sited(recipe, by_limits) and shares:
            shares = _sited_shares(shares, by_limits[recipe.recipe_id])
        fixed = {} if sites.is_sited(recipe, by_limits) else location_inputs.fixed_inputs(recipe, incumbents, setup.recipes, by_limits)
        if fixed:
            tiles = sites.suited_tiles(recipe, setup.tiles, sorted(within) if within is not None else sorted(setup.tiles),
                                       setup.recipe_allowed)
            capacity_by_tile = location_inputs.place_oriented(
                setup, record, area_map, carriage, recipe, fixed,
                [(area, area_runs) for area, area_runs in shares], tiles)
            _add_producers(setup, record, recipe, capacity_by_tile, input_demand, by_limits)
            continue
        if recipe_id in yields:
            shares = _where_it_crops(setup, recipe, shares)
        for area, area_runs in shares:
            capacity_by_tile = location.opening_split(setup, recipe, area, area_runs)
            capacity_by_tile = _at_area_yield(setup, recipe, capacity_by_tile, yields)
            _add_producers(setup, record, recipe, capacity_by_tile, input_demand, by_limits)


def _where_it_crops(setup, recipe, shares):
    """A crop recipe's runs for the market areas where a tile can crop it: an area with none (too dry, too cold)
    is fed by the others, so its runs are shared over them in proportion."""
    growing = [(area, runs) for area, runs in shares if location.opening_split(setup, recipe, area, 1.0)]
    total, kept = math.fsum(runs for _area, runs in shares), math.fsum(runs for _area, runs in growing)
    return [(area, runs * total / kept) for area, runs in growing] if 0.0 < kept < total else shares


def _at_area_yield(setup, recipe, capacity_by_tile, yields) -> Dict[TileId, float]:
    """The runs of a crop recipe, which were counted at the national mean yield, scaled so the tiles they stand on
    (each at its own yield factor) make what the area's share of the national runs would."""
    if recipe.recipe_id not in yields:
        return capacity_by_tile
    factors = {tile: setup.yield_factor_by_recipe_tile.get(recipe_tile_key(recipe.recipe_id, tile), 1.0) for tile in capacity_by_tile}
    total = math.fsum(capacity_by_tile.values())
    made = math.fsum(capacity * factors[tile] for tile, capacity in capacity_by_tile.items())
    if total <= 0.0 or made <= 0.0:
        return capacity_by_tile
    scale = yields[recipe.recipe_id] * total / made
    return {tile: capacity * scale for tile, capacity in capacity_by_tile.items()}


def _add_producers(setup, record, recipe, capacity_by_tile, input_demand, by_limits) -> None:
    """One producer of the recipe on each tile that has people and capacity; its inputs and plant wear are
    the demand later suppliers are placed to meet. `capacity_by_tile` is the runs a year to work; the plant is
    as much larger as the share of it that works at the opening prices and the tile's yield is smaller (opening_income.working_share)."""
    for tile, capacity in capacity_by_tile.items():
        producer_id = "producer:" + recipe_tile_key(recipe.recipe_id, tile)
        if capacity <= 0.0 or not _has_people(record, tile):
            continue
        tile_yield = sites.yield_at(recipe, tile, by_limits, setup.yield_factor_by_recipe_tile.get(
            recipe_tile_key(recipe.recipe_id, tile), 1.0))     # a crop recipe is sized at its tile's yield; the engine adds the weather each year
        working_share = opening_income.working_share(recipe, setup.opening_prices, setup.opening_wages, tile_yield)
        held = record.producers.get(producer_id)
        if held is not None:      # a second share of the runs on the same tile (a pooled area's) adds to the producer
            producer_table.put_producer(record.producers, replaced(
                held, capacity_runs=held.capacity_runs + capacity / working_share,
                expected_sales=held.expected_sales + capacity))
        else:
            producer_table.put_producer(record.producers, Producer(
                agent_id=producer_id, owner=households.cohort_id(tile, _richest_class(record, tile)),
                recipe_id=recipe.recipe_id, tile=tile, capacity_runs=capacity / working_share,
                expected_sales=capacity,
                yield_factor=tile_yield))
        wanted = input_demand.setdefault(tile, {})
        for good, quantity in recipe.inputs.items():
            wanted[good] = wanted.get(good, 0.0) + capacity * quantity
        if recipe.plant_life_years > 0.0:
            for good, quantity in recipe.plant_goods.items():
                wanted[good] = wanted.get(good, 0.0) + capacity * quantity / recipe.plant_life_years


def _stock_producers_with_inputs(setup, record) -> None:
    """Each producer opens holding what it would hold at the start of a year it repeats (opening_resting.resting_input_stock):
    an input another opened producer makes and clears earlier (a smaller input depth than its own outputs) is bought
    in the year, the rest (nothing makes it, or a cycle) is held for the planned runs; and the target stock of its
    outputs (opening_resting.resting_output_stock), so the output rule plans neither a refill nor a run-off."""
    depth = recipes_module.input_depth(setup.recipes)
    made = {good for producer in record.producers.values() for good in setup.recipes[producer.recipe_id].outputs}
    moves = []
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        runs = producer.expected_sales
        own_depth = min((depth.get(good, 0) for good in recipe.outputs), default=0)
        bought = {good for good in recipe.inputs if good in made and depth.get(good, 0) < own_depth}
        moves.extend(GoodsMove(EDGE_PRODUCTION, producer.agent_id, good, producer.tile, quantity, "opening stock of inputs")
                     for good, quantity in opening_resting.resting_input_stock(runs, recipe.inputs, bought).items())
        moves.extend(GoodsMove(EDGE_PRODUCTION, producer.agent_id, good, producer.tile, quantity, "opening stock of output")
                     for good, quantity in opening_resting.resting_output_stock(runs, recipe.outputs).items())
    if moves:
        record.book.move_many(moves)


def _has_people(record, tile) -> bool:
    return any(cohort.tile == tile for cohort in record.cohorts.values())


def _richest_class(record, tile) -> int:
    return ownership.richest_class(record.cohorts.values(), tile) or 0


def _open_merchants(setup, record, prices, final_by_tile) -> None:
    if not setup.opening_population_by_tile:
        return     # no populated tile to base a merchant in
    count = max(1, int(round(len(setup.tiles) * MERCHANTS_PER_TILE)))
    output_value = math.fsum(quantity * prices[good]
                             for good, quantity in opening_runs.national_totals(final_by_tile).items()
                             if prices.get(good) is not None)
    capital = output_value * MERCHANT_CAPITAL_SHARE_OF_OUTPUT / count
    by_population = sorted(setup.opening_population_by_tile, key=lambda tile: (-setup.opening_population_by_tile[tile], tile))
    for index in range(count):
        tile = by_population[index % len(by_population)]
        merchant_id = "merchant:%d" % index
        merchants.put_merchant(record.merchants, Merchant(agent_id=merchant_id, home_tile=tile,
                                                          owner=households.cohort_id(tile, _richest_class(record, tile)),
                                                          capital_base=capital))


def _strike_opening_cash(setup, record, view, extra_spending) -> None:
    """Each agent's opening purse is struck at the mint. A producer's is the year's variable cost of its expected sales
    (the cash `producers_close.working_capital_target` keeps), a merchant's its capital. A household's follows from
    what it owns of those producers (`equity.holdings`, what the spending rule reads as share wealth): the cash that
    brings cash plus share wealth to the wealth target, at which the rule spends exactly its income
    (opening_resting.resting_household_purse; Eurace manual 10.1.3), plus what a household whose plot frees part of its
    budget needs to spend (opening_own.py)."""
    money = setup.currency_id
    transfers: List[Transfer] = []
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        target = working_capital_target(recipe, producer.expected_sales, setup.opening_prices, setup.opening_wages)
        transfers.append(Transfer(EDGE_MINT, producer.agent_id, money, target, "opening coin"))
    for merchant in record.merchants.values():
        transfers.append(Transfer(EDGE_MINT, merchant.agent_id, money, merchant.capital_base, "opening coin"))
    record.book.transfer_many([transfer for transfer in transfers if transfer.amount > 0.0])
    owned = equity.holdings(setup, record, view)
    transfers = []
    for cohort in record.cohorts.values():
        purse = opening_resting.resting_household_purse(cohort.last_year_income, owned.get(cohort.agent_id, 0.0),
                                                       extra_spending=extra_spending.get(cohort.agent_id, 0.0))
        transfers.append(Transfer(EDGE_MINT, cohort.agent_id, money, opening_resting.purse_with_property_income(
            purse, record.capital_markets.property_income.get(cohort.agent_id, 0.0)), "opening coin"))
        households_cohort.change_cohort(record.cohorts, cohort.agent_id, share_wealth=owned.get(cohort.agent_id, 0.0))
    record.book.transfer_many([transfer for transfer in transfers if transfer.amount > 0.0])
