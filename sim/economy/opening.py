"""The economy at the opening: who exists, what they hold, and how much each producer can make.

Initial conditions only. People per tile come from the engine; the opening prices and wages seed
expectations. Producers' capacity is sized so the opening supplies what households demand at those
prices, through the recipes the society already runs (input-output: final demand plus what the
producers of it consume, back to raw materials). Each agent's opening cash is what it wants to hold,
struck at the mint: the money stock is derived, not authored. After this the markets take over.
"""
import math
from typing import Dict, List, Mapping, Tuple

from sim.constants import declare

from . import currency, goods_market, households, households_store, labour_state, location, mint, opening_stores, ownership, sites, unit_cost
from .accounts import Book
from .market_areas import AreaMap
from .market_memory import MarketMemory, YearView, market_key
from .merchants import Merchant
from .producers import Producer
from .producers_close import working_capital_target
from .record import EconomyRecord
from .setup import EconomySetup, labour_area, recipe_tile_key
from .tile_costs import CarriageTable
from .types import EDGE_MINT, EDGE_PRODUCTION, GoodId, GoodsMove, Recipe, TileId, Transfer

OPENING_SPARE_CAPACITY_SHARE = declare(
    "OPENING_SPARE_CAPACITY_SHARE", 0.1, kind="temporary_heuristic",
    unit="share of the opening's required output", source=None, confidence="D",
    why="Producers at the opening can make somewhat more than the opening demands, so a good harvest "
        "or a rise in demand is met from capacity before new plant is built. Real spare capacity "
        "varies by trade and season and is not measured here.")
INPUT_OUTPUT_PASSES = 60
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


def open_economy(setup: EconomySetup) -> Tuple[EconomyRecord, AreaMap, CarriageTable]:
    carriage = setup.carriage_table()
    priced_goods = {good: price for good, price in setup.opening_prices.items()
                    if good in setup.specs and price > 0.0}
    area_map = setup.area_map(carriage)
    memory = _opening_memory(setup, area_map, priced_goods)
    record = EconomyRecord(book=Book(), memory=memory, currency=setup.currency,
                           ways={key: dict(built) for key, built in setup.improvements.items()})
    view = YearView(memory, record.book, area_map, setup.currency_id, labour_area)
    _open_cohorts(setup, record)
    _seed_durable_stocks(setup, record, view)
    final_by_tile = _final_demand(setup, record, view)
    incumbents = incumbent_recipes(setup.recipes, priced_goods, setup.opening_wages, setup.opening_rate)
    runs = required_runs(final_by_tile, incumbents, setup.recipes)
    _place_producers(setup, record, area_map, final_by_tile, incumbents, runs)
    sites.apply_site_limits(record, setup)
    record.workforce = labour_state.opening_workforce(setup, record)
    _open_merchants(setup, record, priced_goods, final_by_tile)
    _strike_opening_cash(setup, record)
    mint.seed_opening_metal(setup, record)
    opening_stores.seed_opening_stores(setup, record, _store_goods(setup, view, area_map, priced_goods))
    record.opening_basket = _national(final_by_tile)
    return record, area_map, carriage


def _store_goods(setup, view, area_map, priced_goods) -> set:
    """The goods fit to hold as wealth at the opening prices, as households choose them."""
    tile = setup.capital_tile
    staple = households_store.staple_price_per_kg(households.need_prices(setup.basket_for(tile), view, tile), setup.specs)
    prices = {good: view.price(good, area_map.area_of(good, tile)) or 0.0 for good in priced_goods}
    return set(households_store.store_candidates(setup.specs, prices, staple)) if math.isfinite(staple) else set()


def _opening_memory(setup, area_map, priced_goods) -> MarketMemory:
    memory = MarketMemory(year=0, rates={setup.currency_id: setup.opening_rate},
                          basket_price_levels={setup.currency_id: 1.0})
    for good, price in priced_goods.items():
        for area in area_map.areas(good):
            memory.prices[market_key(good, area.area_id)] = price
            memory.note_usual_price(market_key(good, area.area_id))
    for trade, wage in setup.opening_wages.items():
        for tile in setup.tiles:
            memory.wages[market_key(trade, labour_area(tile))] = wage
    return memory


def _opening_income_per_head(setup) -> float:
    return setup.opening_wages.get(setup.unskilled_trade, 0.0) * setup.working_hours_per_year * setup.working_share


def _open_cohorts(setup, record) -> None:
    income = _opening_income_per_head(setup)
    for tile, people in sorted(setup.opening_population_by_tile.items()):
        for cohort in households.cohorts_for_tile(tile, people, setup.working_share, setup.gini,
                                                  opening_income_per_capita=income):
            record.cohorts[cohort.agent_id] = cohort


def _opening_bids(setup, record, view):
    """(cohort, bid, price) for what each cohort would buy at the opening prices with the opening income."""
    priced_by_tile = {}
    for cohort in sorted(record.cohorts.values(), key=lambda each: each.agent_id):
        priced = priced_by_tile.setdefault(cohort.tile, households.need_prices(setup.basket_for(cohort.tile), view, cohort.tile))
        income = cohort.last_year_income
        orders = households.goods_orders(cohort, view, income, income, setup.basket_for(cohort.tile), setup.specs,
                                         priced)
        for bid in orders.bids:
            price = view.price(bid.good, bid.area)
            if price:
                yield cohort, bid, price


def _seed_durable_stocks(setup, record, view) -> None:
    """Households open holding the durables they keep in use (dwellings, vessels, tools): the stock their
    expected flow wants over the good's service life. Without it the first year's demand is the whole
    stock built at once, thirty years of walls in one, and the opening staffs for a building boom that is
    never repeated."""
    moves = []
    for cohort, bid, price in _opening_bids(setup, record, view):
        spec = setup.specs.get(bid.good)
        if spec is None or spec.service_life_years <= 0.0 or bid.priority == households_store.STORE_PRIORITY:
            continue     # a store of wealth is seeded from the deposits (opening_stores), not from need
        quantity = bid.floor_quantity + bid.flexible_quantity     # the stock wanted, whatever the cash
        if quantity > 0.0:
            moves.append(GoodsMove(EDGE_PRODUCTION, cohort.agent_id, bid.good, cohort.tile, quantity,
                                   "opening stock of a durable in use"))
    if moves:
        record.book.move_many(moves)


def _final_demand(setup, record, view) -> Dict[TileId, Dict[GoodId, float]]:
    """What each tile's households buy at the opening prices with the opening income."""
    final: Dict[TileId, Dict[GoodId, float]] = {}
    for cohort, bid, price in _opening_bids(setup, record, view):
        demand = final.setdefault(cohort.tile, {})
        demand[bid.good] = demand.get(bid.good, 0.0) + goods_market.quantity_at(bid, price)
    return final


def _national(by_tile: Mapping[TileId, Mapping[GoodId, float]]) -> Dict[GoodId, float]:
    total: Dict[GoodId, float] = {}
    for demand in by_tile.values():
        for good, quantity in demand.items():
            total[good] = total.get(good, 0.0) + quantity
    return dict(sorted(total.items()))


def incumbent_recipes(recipes: Mapping[str, Recipe], prices: Mapping[GoodId, float],
                      wages: Mapping[str, float], rate: float) -> Dict[GoodId, str]:
    """The recipe each good is made by at the opening: the cheapest per unit of that good, a joint
    run's cost shared among its outputs by their value."""
    best: Dict[GoodId, Tuple[float, str]] = {}
    for recipe_id, recipe in sorted(recipes.items()):
        cost = (unit_cost.variable_cost_per_run(recipe, prices, wages)
                + unit_cost.capital_charge_per_run(recipe, prices, wages, rate))
        if not math.isfinite(cost):
            continue
        values = {good: quantity * prices.get(good, 0.0) for good, quantity in recipe.outputs.items()}
        total_value = math.fsum(values.values())
        for good, quantity in recipe.outputs.items():
            if quantity <= 0.0:
                continue
            share = values[good] / total_value if total_value > 0.0 else 1.0 / len(recipe.outputs)
            per_unit = cost * share / quantity
            if good not in best or per_unit < best[good][0]:
                best[good] = (per_unit, recipe_id)
    return {good: recipe_id for good, (_cost, recipe_id) in sorted(best.items())}


def required_runs(final_by_tile, incumbents: Mapping[GoodId, str],
                  recipes: Mapping[str, Recipe]) -> Dict[str, float]:
    """Runs a year of each incumbent recipe that meet final demand and every incumbent's own inputs
    and plant wear (a fixed point of the input-output system)."""
    final = _national(final_by_tile)
    runs: Dict[str, float] = {}
    for _ in range(INPUT_OUTPUT_PASSES):
        required = dict(final)
        for recipe_id, count in runs.items():
            recipe = recipes[recipe_id]
            for good, quantity in recipe.inputs.items():
                required[good] = required.get(good, 0.0) + count * quantity
            if recipe.plant_life_years > 0.0:
                for good, quantity in recipe.plant_goods.items():
                    required[good] = required.get(good, 0.0) + count * quantity / recipe.plant_life_years
        updated: Dict[str, float] = {}
        for good, quantity in sorted(required.items()):
            recipe_id = incumbents.get(good)
            if recipe_id is None or quantity <= 0.0:
                continue
            made = recipes[recipe_id].outputs.get(good, 0.0)
            if made > 0.0:
                updated[recipe_id] = max(updated.get(recipe_id, 0.0), quantity / made)
        if all(abs(updated.get(key, 0.0) - runs.get(key, 0.0)) <= 1e-9 * max(1.0, updated.get(key, 0.0))
               for key in set(updated) | set(runs)):
            return updated
        runs = updated
    return runs


def _main_output(recipe: Recipe, prices: Mapping[GoodId, float]) -> GoodId:
    return max(sorted(recipe.outputs), key=lambda good: recipe.outputs[good] * prices.get(good, 0.0))


def _placement_order(runs, recipes, setup) -> List[str]:
    """Recipes in the order they are placed: a recipe after every recipe that uses what it makes, so the
    users of an input are on the map before its suppliers are placed beside them. A cycle falls back to id order."""
    users = {}
    for recipe_id in runs:
        recipe = recipes[recipe_id]
        for good in list(recipe.inputs) + list(recipe.plant_goods):
            users.setdefault(good, set()).add(recipe_id)
    produced = {recipe_id: _main_output(recipes[recipe_id], setup.opening_prices) for recipe_id in runs}
    ordered: List[str] = []
    waiting = sorted(runs)
    while waiting:
        ready = [recipe_id for recipe_id in waiting
                 if all(user in ordered or user == recipe_id for user in users.get(produced[recipe_id], ()))]
        step = ready or waiting[:1]
        ordered.extend(step)
        waiting = [recipe_id for recipe_id in waiting if recipe_id not in step]
    return ordered


def _place_producers(setup, record, area_map, final_by_tile, incumbents, runs) -> None:
    """Each market area of the recipe's main output gets its share of the runs, sized by the area's share
    of the demand for that good (households' and the already placed producers' that use it as an input; its
    people's share when nobody buys it), spread over its tiles by location.opening_split: one producer per
    (recipe, tile). An input is therefore opened where its users are, with the supply their capacity needs,
    not where people happen to live (a good too cheap to carry has a market the size of a tile)."""
    population = setup.opening_population_by_tile
    by_limits = sites.limits_by_recipe(setup.site_limits)
    input_demand: Dict[TileId, Dict[GoodId, float]] = {}
    for recipe_id in _placement_order(runs, setup.recipes, setup):
        count = runs[recipe_id]
        recipe = setup.recipes[recipe_id]
        main = _main_output(recipe, setup.opening_prices)
        areas = area_map.areas(main) if main in area_map.goods() else ()
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
            shares = [(shares[0][0], count)]               # a sited recipe's tiles are the limits', in any area
        for area, area_runs in shares:
            capacity_by_tile = location.opening_split(setup, recipe, area, area_runs * (1.0 + OPENING_SPARE_CAPACITY_SHARE))
            for tile, capacity in capacity_by_tile.items():
                producer_id = "producer:" + recipe_tile_key(recipe_id, tile)
                if capacity <= 0.0 or producer_id in record.producers or not _has_people(record, tile):
                    continue
                record.producers[producer_id] = Producer(
                    agent_id=producer_id, owner=households.cohort_id(tile, _richest_class(record, tile)),
                    recipe_id=recipe_id, tile=tile, capacity_runs=capacity,
                    expected_sales=capacity / (1.0 + OPENING_SPARE_CAPACITY_SHARE),
                    yield_factor=sites.yield_at(recipe, tile, by_limits, setup.yield_factor_by_recipe_tile.get(
                        recipe_tile_key(recipe_id, tile), 1.0)))
                wanted = input_demand.setdefault(tile, {})
                for good, quantity in recipe.inputs.items():
                    wanted[good] = wanted.get(good, 0.0) + capacity * quantity
                if recipe.plant_life_years > 0.0:
                    for good, quantity in recipe.plant_goods.items():
                        wanted[good] = wanted.get(good, 0.0) + capacity * quantity / recipe.plant_life_years


def _has_people(record, tile) -> bool:
    return any(cohort.tile == tile for cohort in record.cohorts.values())


def _richest_class(record, tile) -> int:
    return ownership.richest_class(record.cohorts.values(), tile) or 0


def _open_merchants(setup, record, prices, final_by_tile) -> None:
    count = max(1, int(round(len(setup.tiles) * MERCHANTS_PER_TILE)))
    output_value = math.fsum(quantity * prices.get(good, 0.0)
                             for good, quantity in _national(final_by_tile).items())
    capital = output_value * MERCHANT_CAPITAL_SHARE_OF_OUTPUT / count
    by_population = sorted(setup.opening_population_by_tile, key=lambda tile: (-setup.opening_population_by_tile[tile], tile))
    for index in range(count):
        tile = by_population[index % len(by_population)]
        merchant_id = "merchant:%d" % index
        record.merchants[merchant_id] = Merchant(agent_id=merchant_id, home_tile=tile,
                                                 owner=households.cohort_id(tile, _richest_class(record, tile)),
                                                 capital_base=capital)


def _strike_opening_cash(setup, record) -> None:
    """Each agent's opening purse is what it wants to hold, struck at the mint."""
    money = setup.currency_id
    rate = setup.opening_rate
    transfers: List[Transfer] = []
    for cohort in record.cohorts.values():
        target = currency.cash_balance_target(cohort.last_year_income, rate, 0.0)
        transfers.append(Transfer(EDGE_MINT, cohort.agent_id, money, target, "opening coin"))
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        target = working_capital_target(recipe, producer.capacity_runs, setup.opening_prices, setup.opening_wages)
        transfers.append(Transfer(EDGE_MINT, producer.agent_id, money, target, "opening coin"))
    for merchant in record.merchants.values():
        transfers.append(Transfer(EDGE_MINT, merchant.agent_id, money, merchant.capital_base, "opening coin"))
    record.book.transfer_many([transfer for transfer in transfers if transfer.amount > 0.0])
