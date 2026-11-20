"""A producer's input orders, re-sized to the runs its hired hours can make (the clearing rule set).

The plan orders inputs for the runs it expected at last year's wage. Under the clearing set the hours a producer hires
answer this year's wage (labour_demand.py), so they can staff more runs than the plan, or fewer. Between the labour
clearing and the goods markets each input order is therefore re-sized: the units the plan's runs needed (what it
ordered and what it held), scaled to the runs the hired hours make, less what is held; and the coin the producer has
left after wages, less what the plant it means to rebuild costs (plant_coin.py), is split over its orders by their
value, as the plan split what it expected to have left. An input
the plan did not order (its stock covered the planned runs) is not ordered now either: the stock then holds the runs."""
from typing import Optional

import numpy as np

from . import plant_coin, practice
from .goods_production import read_stocks
from .goods_production_reads import hours_hired_of
from .plan_table import plan_sums
from .staffed_runs import staffed_runs

QUANTITY, REFERENCE_PRICE, BUDGET = 0, 2, 4      # columns of a plan's bid figures (plan_table.BidColumns)


def runs_the_hours_make(ordered_runs: float, most_runs: float, staffed: Optional[float]) -> float:
    """The runs a producer's inputs are ordered for once its hours are hired: the runs those hours staff, no more than
    the most its schedule would staff; the runs the plan ordered for where the recipe hires no hours."""
    if staffed is None:
        return ordered_runs
    return max(0.0, min(staffed, most_runs))


def resized_quantities(quantities: np.ndarray, stocks: np.ndarray, ordered_runs: np.ndarray, runs_to_make: np.ndarray) -> np.ndarray:
    """Units of each input to order for `runs_to_make`, where the plan ordered `quantities` for `ordered_runs` holding
    `stocks`: what the ordered runs needed in all, scaled to the runs to make, less what is held; never under nothing.
    An order whose plan had no runs is left as it is."""
    needed = quantities + stocks
    scale = np.divide(runs_to_make, ordered_runs, out=np.ones_like(runs_to_make), where=ordered_runs > 0.0)
    return np.where(ordered_runs > 0.0, np.maximum(0.0, needed * scale - stocks), quantities)


def budgets_by_value(values: np.ndarray, owner: np.ndarray, coin_of_owner: np.ndarray) -> np.ndarray:
    """Each order's budget: its owner's coin split over the owner's orders by their value (`owner`: the place of each
    order's owner in `coin_of_owner`); nothing where the owner's orders are worth nothing."""
    totals = np.bincount(owner, weights=values, minlength=len(coin_of_owner))
    share = np.divide(values, totals[owner], out=np.zeros_like(values), where=totals[owner] > 0.0)
    return np.maximum(0.0, coin_of_owner[owner]) * share


def leave_as_planned(_setup, _record, _view, _plans, _ledger) -> None:
    """The search rule set's orders stay as the plan made them."""


def resize_to_hired_hours(setup, record, view, plans, ledger) -> None:
    """Re-size the input orders of `plans` (in place) to the runs each producer's hired hours make, and split the coin
    it has for its runs (plant_coin.py) over them; the plan's budget totals are worked out again."""
    bids = plans.bids
    if not len(bids.position):
        return
    ids, store, book = plans.ids, record.producers, record.book
    places = sorted(set(bids.position.tolist()))
    recipes = [practice.recipe_for(setup.recipes[store[ids[place]].recipe_id], store[ids[place]].crew_runs) for place in places]
    hired = hours_hired_of(ledger, [(ids[place], tuple(recipe.labour_hours)) for place, recipe in zip(places, recipes)])
    runs_to_make = np.array(plans.ordered_runs, dtype=np.float64)
    for place, recipe, hours in zip(places, recipes, hired):
        runs_to_make[place] = runs_the_hours_make(plans.ordered_runs[place], plans.runs[place], staffed_runs(recipe.labour_hours, hours))
    owner = bids.position
    cells = [(ids[place], plans.good_names[good], plans.tile_names[tile])
             for place, good, tile in zip(owner.tolist(), bids.good.tolist(), bids.tile.tolist())]
    stocks = np.asarray(read_stocks(book, cells), dtype=np.float64)
    figures = bids.figures
    figures[:, QUANTITY] = resized_quantities(figures[:, QUANTITY], stocks, np.array(plans.ordered_runs, dtype=np.float64)[owner], runs_to_make[owner])
    coin = np.zeros(len(ids))
    held = book.balances_of([ids[place] for place in places], setup.currency_id).tolist()
    coin[places] = [plant_coin.coin_for_runs(setup, record, view, store[ids[place]], amount) for place, amount in zip(places, held)]
    figures[:, BUDGET] = budgets_by_value(figures[:, QUANTITY] * figures[:, REFERENCE_PRICE], owner, coin)
    plans.budget_total, plans.outlay_total = plan_sums(plans.wage_line, np.ascontiguousarray(figures[:, BUDGET]), plans.bid_start)
