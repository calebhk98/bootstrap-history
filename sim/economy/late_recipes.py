"""Recipes a society can run that its economy did not open with: a technique gained later.

The port builds a fresh setup from the society's present techniques; `admit_recipes` takes from it what
the running economy lacks: the new recipes and goods, the goods' specs and opening prices. A good
that had no price has no market, so its market areas are made now and its markets start at that price.
Producers for the new recipes enter through the ordinary entry rules.

Standalone: the setup, record and area map of this package.
"""
from .market_memory import market_key


def admit_recipes(economy, source) -> bool:
    """Give `economy` the recipes, goods and prices `source` (an EconomySetup) has that it lacks; False when
    it lacks none. Nothing the economy already has is changed."""
    setup = economy.setup
    new_recipes = [recipe_id for recipe_id in sorted(source.recipes) if recipe_id not in setup.recipes]
    new_goods = [good for good in sorted(source.opening_prices) if good not in setup.opening_prices]
    if not new_recipes and not new_goods:
        return False
    for recipe_id in new_recipes:
        setup.recipes[recipe_id] = source.recipes[recipe_id]
        if recipe_id in source.land_per_run:
            setup.land_per_run[recipe_id] = source.land_per_run[recipe_id]
    for good, spec in source.specs.items():
        setup.specs.setdefault(good, spec)
    for trade, wage in source.opening_wages.items():
        setup.opening_wages.setdefault(trade, wage)
    setup.recipes_by_country = {country: tuple(recipes) for country, recipes in source.recipes_by_country.items()}
    for good in new_goods:
        setup.opening_prices[good] = source.opening_prices[good]
    if new_goods:
        economy.rebuild_market_areas()
        _open_markets(economy, new_goods)
    return True


def _open_markets(economy, goods) -> None:
    """Each new good's markets remember its opening price, as the opening's do."""
    memory = economy.record.memory
    for good in goods:
        for area in economy.area_map.areas(good):
            key = market_key(good, area.area_id)
            memory.prices[key] = economy.setup.opening_prices[good]
            memory.note_usual_price(key)
