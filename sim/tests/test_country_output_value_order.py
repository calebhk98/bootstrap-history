"""The value of a country's output does not depend on the order its producers are held in (a loaded game holds them in saved order)."""
QUICK_TOPIC = True

from types import SimpleNamespace
from itertools import permutations

from .harness import *  # noqa: F401,F403
from sim.economy import country_figures

PRICES = {"grain": 0.1, "cloth": 0.7, "iron": 1.0 / 3.0}
RECIPES = {"farm": SimpleNamespace(outputs={"grain": 1.3}), "loom": SimpleNamespace(outputs={"cloth": 0.37, "iron": 0.11}),
           "forge": SimpleNamespace(outputs={"iron": 2.9})}


def producer(recipe_id, runs, yield_factor):
    return SimpleNamespace(tile="t", recipe_id=recipe_id, capacity_runs=runs, last_runs=runs, yield_factor=yield_factor)


def value_in_order(producers):
    economy = SimpleNamespace(record=SimpleNamespace(producers=dict(enumerate(producers))), setup=SimpleNamespace(recipes=RECIPES))
    saved = country_figures.country_tiles, country_figures.prices
    country_figures.country_tiles, country_figures.prices = (lambda economy, country: {"t"}), (lambda economy, country: PRICES)
    try:
        return country_figures.output_value(economy, "c")
    finally:
        country_figures.country_tiles, country_figures.prices = saved


held = [producer(recipe, runs, factor) for recipe, runs, factor in (
    ("farm", 1e12 + 0.3, 0.97), ("loom", 3.1e3, 1.01), ("forge", 1e-3, 0.5), ("farm", 7.77e5, 1.0), ("loom", 1e12 / 3.0, 0.9), ("forge", 0.123456789, 1.0))]
totals = {value_in_order(list(order)) for order in permutations(held)}
check("the output value is the same in every order of the producers", len(totals) == 1, totals)
check("with no producers there is no output value", value_in_order([]) is None)
