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
    it lacks none. Nothing the economy already has is changed; its setup is replaced by one that has them."""
    setup = economy.setup
    new_recipes = [recipe_id for recipe_id in sorted(source.recipes) if recipe_id not in setup.recipes]
    new_goods = [good for good in sorted(source.opening_prices) if good not in setup.opening_prices]
    if not new_recipes and not new_goods:
        return False
    added = set(new_recipes)
    economy.change_setup(
        recipes={**setup.recipes, **{recipe_id: source.recipes[recipe_id] for recipe_id in new_recipes}},
        land_per_run={**setup.land_per_run, **{recipe_id: source.land_per_run[recipe_id] for recipe_id in new_recipes
                                               if recipe_id in source.land_per_run}},
        yield_factor_by_recipe_tile={**setup.yield_factor_by_recipe_tile,
                                     **{key: factor for key, factor in source.yield_factor_by_recipe_tile.items()
                                        if key.partition("@")[0] in added}},
        specs={**setup.specs, **{good: spec for good, spec in source.specs.items() if good not in setup.specs}},
        opening_wages={**setup.opening_wages, **{trade: wage for trade, wage in source.opening_wages.items()
                                                 if trade not in setup.opening_wages}},
        recipes_by_country={country: tuple(recipes) for country, recipes in source.recipes_by_country.items()},
        opening_prices={**setup.opening_prices, **{good: source.opening_prices[good] for good in new_goods}})
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
            memory.set_price(key, economy.setup.opening_prices[good])
            memory.note_usual_price(key)
