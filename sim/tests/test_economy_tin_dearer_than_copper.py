"""Complaint 511: tin's price follows from the gravel its deposits must be worked through, so in a Rome game the
price shown for tin over copper's is not below the ratio of the labour their recipes embody (tin, a metal of
few deposits, must be dug from a great weight of lean gravel). Measured on the opening year, before any
unsold seller's ask has drifted below cost. The aged-game relation (tin not below copper after years) waits on
stage 7 of docs/architecture/ONE_PRICE_OWNER_PLAN.md (unsold asks held near cost, Complaints/507); do not weaken this check
to stand in for it."""
from .harness import *  # noqa: F401,F403

from sim.economy import api as economy_api
from sim.economy.protocols import YearInputs

DEARER_METAL = "tin_kg"
CHEAPER_METAL = "copper_kg"


def embodied_labour_hours(recipes, good, memo=None):
    """Hours of labour, through every input, in a unit of `good` by its cheapest recipe."""
    memo = {} if memo is None else memo
    if good in memo:
        return memo[good]
    memo[good] = float("inf")                 # a loop in the recipes costs nothing to follow twice
    best = float("inf")
    for recipe in recipes.values():
        made = recipe.outputs.get(good, 0.0)
        if made <= 0.0:
            continue
        hours = sum(recipe.labour_hours.values()) + sum(
            amount * embodied_labour_hours(recipes, input_good, memo) for input_good, amount in recipe.inputs.items())
        best = min(best, hours / made)
    memo[good] = best
    return best


def opening_year_tin_over_copper():
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("rome_100ad"))
    economy = game.economy.agent.economy()
    economy.step(YearInputs(year=0, population_by_tile={}, working_age_share=0.6,
                            yield_factor_by_producer={}, engine_orders={}))
    shown, _stale = economy_api.shown_prices_of(economy)
    labour = {metal: embodied_labour_hours(economy.setup.recipes, metal) for metal in (DEARER_METAL, CHEAPER_METAL)}
    return shown[DEARER_METAL] / shown[CHEAPER_METAL], labour[DEARER_METAL] / labour[CHEAPER_METAL]


def tin_is_not_cheaper_than_its_labour_against_copper():
    price_ratio, labour_ratio = opening_year_tin_over_copper()
    return price_ratio >= labour_ratio, "shown tin over copper %.3f, embodied labour ratio %.3f" % (price_ratio, labour_ratio)


slow_check("Complaint 511: tin shows no cheaper against copper than the labour its recipe embodies",
           tin_is_not_cheaper_than_its_labour_against_copper)
