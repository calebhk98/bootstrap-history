"""What bounds a seller's ask from above: the most its buyers will pay before they have something better to do.

A good's buyers are households (a need the good meets) and producers (recipes that use it as an input). Each kind of buyer
gives a ceiling, and the good's ceiling is the highest of them (the buyers who stay at the highest price set it):

  * a household need: the price at which the good costs per need unit what the cheapest other good of the need does (that
    good's price or its making cost, `alternative_ceiling`); with no other good in the need, the highest price at which any
    household bid still takes units (`buyer_limit`: its budget over its floor units, held to its own maximum price);
  * a recipe using the good as an input: the price at which the recipe costs per unit of its main output what the cheapest
    recipe for the same output without the good costs, never more than the run's revenue less its other costs, the most
    the buyer can pay and break even (`recipe_ceiling`); a recipe with no such alternative is bound by that value alone.

Making the seller's own good is not counted: that is a newcomer entering the market (`entry_trial.py`). A good none of
whose buyers gives a ceiling has none, and `band_multiple` leaves its seller no room above cost; it never leaves it unbounded.
Everything above `AskAlternatives` is pure; `AskAlternatives` reads a game's prices once.
"""
import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Optional, Sequence

from sim.world.need_basket import NeedSpec

from . import unit_cost
from .ask_adjust import NO_BOUND_MULTIPLE
from .types import Recipe

CAUSE_NO_NEED = "serves_no_need"                    # the good meets no household need
CAUSE_NO_ALTERNATIVE = "no_alternative_in_need"     # a need it meets has no other priced or makeable good
CAUSE_NO_BUYER = "no_buyer_to_bound_it"             # no household bid and no recipe using it gives a ceiling


@dataclass(frozen=True)
class AskCeiling:
    price: Optional[float]      # most a unit may be asked before buyers turn elsewhere; None when nothing bounds it
    cause: Optional[str]        # why there is no price (None when there is one)


def _cost_per_need_unit(other: str, effect: float, price_of: Callable[[str], Optional[float]],
                        making_cost_of: Callable[[str], Optional[float]]) -> Optional[float]:
    """What a unit of need costs through `other`: the lower of its price and its making cost, over its effectiveness."""
    options = [value for value in (price_of(other), making_cost_of(other)) if value is not None and math.isfinite(value) and value > 0.0]
    return min(options) / effect if options and effect > 0.0 else None


def alternative_ceiling(good: str, needs: Sequence[NeedSpec], price_of: Callable[[str], Optional[float]],
                        making_cost_of: Callable[[str], Optional[float]]) -> AskCeiling:
    """The price of `good` at which its household buyers do as well through the cheapest other good of each need it meets. A
    good meeting several needs is bounded by the highest of its needs' ceilings (the buyers of each leave at their own), and
    by none if any one of those needs offers no alternative."""
    ceilings = []
    for need in needs:
        effect = dict(need.goods).get(good, 0.0)
        if effect <= 0.0:
            continue
        costs = [cost for other, other_effect in need.goods if other != good
                 for cost in [_cost_per_need_unit(other, other_effect, price_of, making_cost_of)] if cost is not None]
        if not costs:
            return AskCeiling(None, CAUSE_NO_ALTERNATIVE)
        ceilings.append(min(costs) * effect)
    return AskCeiling(max(ceilings), None) if ceilings else AskCeiling(None, CAUSE_NO_NEED)


def buyer_limit(floors: Sequence[float], flexibles: Sequence[float], budgets: Sequence[float],
                maximums: Sequence[float]) -> Optional[float]:
    """The highest price at which any of the bids (columns of the order tables) still takes units: a bid's budget over the
    units it needs whatever the price (its floor, else what it asks for beyond it), held to its own maximum price. A bid with
    no budget or nothing wanted takes none. None when no bid does."""
    limits = []
    for floor, flexible, budget, maximum in zip(floors, flexibles, budgets, maximums):
        wanted = floor if floor > 0.0 else flexible
        if budget <= 0.0 or wanted <= 0.0:
            continue
        limits.append(min(maximum, budget / wanted))
    return max(limits) if limits else None


def recipe_ceiling(good: str, recipe: Recipe, makers: Sequence[Recipe], prices: Mapping[str, float], wages: Mapping[str, float],
                   interest_rate: float) -> Optional[float]:
    """The most a maker running `recipe` pays for a unit of `good` (one of its inputs) at today's `prices`, `wages` and
    `interest_rate`. `makers` are the recipes that yield the recipe's main output (its most valuable one). Two bounds:

      * the value: the run's revenue less its cost with the good free, per unit of the good, which is where the run only just
        breaks even (None when the outputs cannot be priced);
      * the switch, where some maker in `makers` does not use the good: the price at which the recipe costs per unit of its
        main output what the cheapest such maker's costs. Cost is linear in the good's price, so it is read at two prices.

    The lower applies; None when the recipe can never pay (either bound is not above zero) or cannot be priced."""
    quantity = recipe.inputs.get(good, 0.0)
    if quantity <= 0.0:
        return None
    free, one = dict(prices), dict(prices)
    free[good], one[good] = 0.0, 1.0
    run_cost = unit_cost.variable_cost_per_run(recipe, free, wages) + unit_cost.capital_charge_per_run(recipe, free, wages, interest_rate)
    value = None
    revenue = unit_cost.revenue_per_run(recipe, prices)
    if revenue > 0.0 and math.isfinite(run_cost):
        value = (revenue - run_cost) / quantity
    switch = None
    main = main_output(recipe, prices)
    alternatives = [unit_cost.full_cost_per_unit(other, main, prices, prices, wages, interest_rate)
                    for other in makers if other is not recipe and good not in other.inputs]
    alternatives = [cost for cost in alternatives if math.isfinite(cost)]
    if alternatives:
        at_free = unit_cost.full_cost_per_unit(recipe, main, prices, free, wages, interest_rate)
        at_one = unit_cost.full_cost_per_unit(recipe, main, prices, one, wages, interest_rate)
        if math.isfinite(at_free) and math.isfinite(at_one) and at_one > at_free:
            switch = (min(alternatives) - at_free) / (at_one - at_free)
    bounds = [bound for bound in (value, switch) if bound is not None]
    ceiling = min(bounds) if bounds else None
    return ceiling if ceiling is not None and ceiling > 0.0 else None


def main_output(recipe: Recipe, prices: Mapping[str, float]) -> str:
    """The output of the recipe worth most per run at `prices` (an unpriced one counts for nothing; ties by name)."""
    return max(sorted(recipe.outputs), key=lambda good: recipe.outputs[good] * (prices.get(good) or 0.0))


def band_multiple(substitution: float, ceiling: AskCeiling, own_cost: Optional[float]) -> float:
    """The most, as a multiple of a unit's cost, a seller's ask may be. Where the buyers give a ceiling, the lower of that
    ceiling over the seller's cost `own_cost` (never below one: the seller's break-even) and the substitution markup (the
    constant-elasticity monopolist's, when buyers substitute more than one for one). With no ceiling, the markup if
    it is derived, else `NO_BOUND_MULTIPLE`: nothing is known to let the seller ask above what a unit costs it."""
    markup = substitution / (substitution - 1.0) if substitution > 1.0 else None
    if ceiling.price is not None and own_cost is not None and math.isfinite(own_cost) and own_cost > 0.0:
        alternative = max(NO_BOUND_MULTIPLE, ceiling.price / own_cost)
        return alternative if markup is None else min(markup, alternative)
    return NO_BOUND_MULTIPLE if markup is None else markup


NO_CEILING = AskCeiling(None, CAUSE_NO_BUYER)     # for a caller that has not read the year's prices


def good_ceiling(household: AskCeiling, household_limit: Optional[float], recipe_ceilings: Sequence[Optional[float]]) -> AskCeiling:
    """The good's ceiling from its buyers: the highest of the household leg (`household`, else the bids' `household_limit` for a
    good alone in its need) and the recipes' (`recipe_ceiling` of each recipe using it, None for one that gives none)."""
    legs: List[float] = [bound for bound in recipe_ceilings if bound is not None]
    if household.price is not None:
        legs.append(household.price)
    elif household.cause == CAUSE_NO_ALTERNATIVE and household_limit is not None:
        legs.append(household_limit)
    return AskCeiling(max(legs), None) if legs else NO_CEILING


class AskAlternatives:
    """The year's ceilings for the goods of a game: the national prices, wages and making costs, read on first use, and each
    good's ceiling and band multiple per tile worked out once. `record.goods.buyer_limits` holds the highest price the
    household bids for a good took units at when it last cleared."""

    def __init__(self, setup, record):
        self.setup, self.record = setup, record
        self._prices: Optional[Dict[str, float]] = None
        self._costs: Optional[Dict[str, float]] = None
        self._wages: Optional[Dict[str, float]] = None
        self._rate = math.nan
        self._users: Optional[Dict[str, List[Recipe]]] = None
        self._ceilings: Dict[tuple, AskCeiling] = {}
        self._multiples: Dict[tuple, float] = {}

    def _read(self) -> None:
        if self._prices is None:
            from .national_prices import national_prices
            from .notional import costing_wages, making_costs
            self._prices, self._costs = national_prices(self.record), making_costs(self.setup, self.record)
            self._wages = costing_wages(self.setup, self.record)
            self._rate = self.record.memory.rates[self.setup.currency_id]

    def _users_of(self, good: str) -> List[Recipe]:
        """The recipes that use `good` as an input."""
        if self._users is None:
            self._users = {}
            for recipe in self.setup.recipes.values():
                for each in recipe.inputs:
                    self._users.setdefault(each, []).append(recipe)
        return self._users.get(good, [])

    def _price(self, good: str) -> Optional[float]:
        self._read()
        return self._prices.get(good)

    def _cost(self, good: str) -> Optional[float]:
        self._read()
        return self._costs.get(good)

    def ceiling(self, good: str, tile: str) -> AskCeiling:
        """The good's `good_ceiling` for the people of `tile`; prices are read only for a good that has a buyer to bound it."""
        key = (good, tile)
        found = self._ceilings.get(key)
        if found is None:
            household = alternative_ceiling(good, self.setup.basket_for(tile).needs, self._price, self._cost)
            limit = self.record.goods.buyer_limits.get(good)
            from .recipes import recipes_making
            bounds = []
            for recipe in self._users_of(good):
                self._read()
                makers = recipes_making(self.setup.recipes, main_output(recipe, self._prices))
                bounds.append(recipe_ceiling(good, recipe, makers, self._prices, self._wages, self._rate))
            found = self._ceilings[key] = good_ceiling(household, limit, bounds)
        return found

    def multiple(self, good: str, tile: str) -> float:
        """The good's band multiple on `tile` (`band_multiple`), scaled against what the good costs to make at today's prices."""
        key = (good, tile)
        found = self._multiples.get(key)
        if found is None:
            ceiling = self.ceiling(good, tile)
            own_cost = self._cost(good) if ceiling.price is not None else None
            found = self._multiples[key] = band_multiple(self.setup.basket_for(tile).substitution, ceiling, own_cost)
        return found
