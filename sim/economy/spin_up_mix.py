"""What a spin-up year's economy is made of, for `spin-up-trace --stages` (sim/markets/spin_up_mix_table.py): hours
hired and idle by trade, runs and capacity by recipe, what each recipe made of the goods several recipes make, and
producers' stock and the year's output by good at the opening prices. Only reads; the settle test does not use it."""
from typing import Dict, Iterable, Mapping, Sequence, Tuple

from .market_memory import KEY_SEPARATOR
from .notional import recently_traded_goods


def hours_by_trade(keys: Sequence[str], hired: Sequence[float], idle: Sequence[float]) -> Dict[str, Tuple[float, float]]:
    """{trade: (hours hired, hours left idle)} over the labour markets `keys` (trade and area joined by the market
    key's separator), whose hired and idle hours are given in the same order."""
    totals: Dict[str, Tuple[float, float]] = {}
    for key, bought, unsold in zip(keys, hired, idle):
        trade = key.split(KEY_SEPARATOR, 1)[0]
        before = totals.get(trade, (0.0, 0.0))
        totals[trade] = (before[0] + bought, before[1] + unsold)
    return totals


def runs_by_recipe(producers: Iterable[Tuple[str, float, float]]) -> Dict[str, Tuple[float, float]]:
    """{recipe: (runs worked, capacity in runs)} over `producers`, each (recipe, runs worked last year, capacity); runs
    below nothing (a producer that has not run) count as none."""
    totals: Dict[str, Tuple[float, float]] = {}
    for recipe_id, runs, capacity in producers:
        before = totals.get(recipe_id, (0.0, 0.0))
        totals[recipe_id] = (before[0] + max(0.0, runs), before[1] + max(0.0, capacity))
    return totals


def made_by_recipe(runs: Mapping[str, Tuple[float, float]], outputs_by_recipe: Mapping[str, Mapping[str, float]]) -> Dict[str, Dict[str, float]]:
    """{good: {recipe: quantity made}} for the goods more than one recipe of `outputs_by_recipe` ({recipe: {good:
    quantity per run}}) makes: each recipe's runs worked (`runs_by_recipe`) times its output a run, before any yield
    factor. A recipe with no runs is in it at nothing, so a route that stopped still shows."""
    makers: Dict[str, list] = {}
    for recipe_id in sorted(outputs_by_recipe):
        for good in outputs_by_recipe[recipe_id]:
            makers.setdefault(good, []).append(recipe_id)
    return {good: {recipe_id: runs.get(recipe_id, (0.0, 0.0))[0] * outputs_by_recipe[recipe_id][good] for recipe_id in recipe_ids}
            for good, recipe_ids in sorted(makers.items()) if len(recipe_ids) > 1}


def value_by_good(quantities: Mapping[str, float], prices: Mapping[str, float]) -> Dict[str, float]:
    """{good: quantity times price} for the goods of `quantities` that `prices` holds and that have some quantity."""
    return {good: quantity * prices[good] for good, quantity in sorted(quantities.items()) if good in prices and quantity != 0.0}


def stock_by_good(holdings_by_agent: Iterable[Mapping[str, Mapping[str, float]]]) -> Dict[str, float]:
    """{good: quantity held} summed over each agent's {good: {tile: quantity}}."""
    totals: Dict[str, float] = {}
    for goods in holdings_by_agent:
        for good, by_tile in goods.items():
            totals[good] = totals.get(good, 0.0) + sum(by_tile.values())
    return totals


def basket_costs(prices: Mapping[str, float], base: Mapping[str, float], basket: Mapping[str, float],
                 recent: Iterable[str]) -> Dict[str, Tuple[float, float]]:
    """{good: (what the basket's quantity of it costs at `prices`, what it cost at the `base` prices)} for the goods the
    fixed-basket price level counts in a year (`currency.basket_price_level` over the goods of `recent`): those of the
    basket that traded recently and hold a price now and at the base. The level is the first column's sum over the second's."""
    counted = set(recent)
    return {good: (prices[good] * quantity, base[good] * quantity) for good, quantity in sorted(basket.items())
            if good in counted and good in prices and good in base}


def year_mix(setup, record, outcome) -> dict:
    """The year just stepped: {"hours_by_trade", "runs_by_recipe", "made_by_recipe", "stock_by_good" and
    "output_by_good" (both at the opening prices), "basket_costs" (what the price level was made of)}."""
    keys = sorted(record.labour.hours_idle)
    runs = runs_by_recipe((producer.recipe_id, producer.last_runs, producer.capacity_runs) for producer in record.producers.values())
    held = stock_by_good(record.book.holdings(agent)["goods"] for agent in record.producers)
    return {"hours_by_trade": hours_by_trade(keys, record.labour.hours_cleared_in_markets(keys), [record.labour.hours_idle[key] for key in keys]),
            "runs_by_recipe": runs,
            "made_by_recipe": made_by_recipe(runs, {recipe_id: recipe.outputs for recipe_id, recipe in setup.recipes.items()}),
            "stock_by_good": value_by_good(held, setup.opening_prices),
            "output_by_good": value_by_good(outcome.output, setup.opening_prices),
            "basket_costs": basket_costs(outcome.prices, record.goods.index_base_prices or setup.opening_prices,
                                         record.goods.opening_basket, recently_traded_goods(record.memory))}
