"""What bounds a seller's ask from above: the cost to its buyers of their cheapest other way to meet the same need.

A good serves one or more needs (`sim/world/need_basket.py`). Buyers of it turn to another good of the same need once it costs
more per need unit than that one: the other good's market price, or what it costs to make from its recipe at today's prices
(`notional.making_costs`), whichever is lower. The price at which the seller's good costs buyers as much per need unit as the
cheapest such good is the ceiling on its ask. Making the seller's own good is not counted here: that is a newcomer entering the
market, which `entry_trial.py` decides.

Where the good has no other good in its need to turn to (or serves no need, as an intermediate good does not), no alternative
bounds it: `AskCeiling.cause` says so and the stated multiple (`ASK_BAND_CEILING`) stands in until the buyers' budget bounds it.
Everything here is pure; `AskAlternatives` reads a game's prices once per year.
"""
import math
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Sequence

from sim.world.need_basket import NeedSpec

from .ask_adjust import ASK_BAND_CEILING

CAUSE_NO_NEED = "serves_no_need"                    # the good meets no household need, so no other good stands in for it
CAUSE_NO_ALTERNATIVE = "no_alternative_in_need"     # a need it meets has no other priced or makeable good


@dataclass(frozen=True)
class AskCeiling:
    price: Optional[float]      # most a unit may be asked before buyers turn to their cheapest alternative; None when none exists
    cause: Optional[str]        # why there is no price (None when there is one)


NO_ALTERNATIVES = AskCeiling(None, CAUSE_NO_ALTERNATIVE)     # for a caller that has not read the year's prices


def _cost_per_need_unit(other: str, effect: float, price_of: Callable[[str], Optional[float]],
                        making_cost_of: Callable[[str], Optional[float]]) -> Optional[float]:
    """What a unit of need costs through `other`: the lower of its price and its making cost, over its effectiveness."""
    options = [value for value in (price_of(other), making_cost_of(other)) if value is not None and math.isfinite(value) and value > 0.0]
    return min(options) / effect if options and effect > 0.0 else None


def alternative_ceiling(good: str, needs: Sequence[NeedSpec], price_of: Callable[[str], Optional[float]],
                        making_cost_of: Callable[[str], Optional[float]]) -> AskCeiling:
    """The price of `good` at which its buyers do as well through the cheapest other good of each need it meets. A good
    meeting several needs is bounded by the highest of its needs' ceilings (the buyers of each leave at their own), and by
    none if any one of those needs offers no alternative."""
    ceilings = []
    for need in needs:
        effects = dict(need.goods)
        effect = effects.get(good, 0.0)
        if effect <= 0.0:
            continue
        costs = [cost for other, other_effect in need.goods if other != good
                 for cost in [_cost_per_need_unit(other, other_effect, price_of, making_cost_of)] if cost is not None]
        if not costs:
            return AskCeiling(None, CAUSE_NO_ALTERNATIVE)
        ceilings.append(min(costs) * effect)
    return AskCeiling(max(ceilings), None) if ceilings else AskCeiling(None, CAUSE_NO_NEED)


def band_multiple(substitution: float, ceiling: AskCeiling, own_cost: Optional[float]) -> float:
    """The most, as a multiple of a unit's cost, a seller's ask may be. Where an alternative bounds the good, the lower of
    that ceiling over the seller's cost `own_cost` (never below one: the seller's break-even) and the substitution markup
    (the constant-elasticity monopolist's, when buyers substitute more than one for one). Where none does, the markup if it
    is derived, never past the stated multiple, else the stated multiple."""
    markup = substitution / (substitution - 1.0) if substitution > 1.0 else None
    if ceiling.price is not None and own_cost is not None and math.isfinite(own_cost) and own_cost > 0.0:
        alternative = max(1.0, ceiling.price / own_cost)
        return alternative if markup is None else min(markup, alternative)
    return ASK_BAND_CEILING if markup is None else min(markup, ASK_BAND_CEILING)


class AskAlternatives:
    """The year's alternatives for the goods of a game: the national prices and the making costs, read on first use, and
    each good's ceiling and band multiple per tile worked out once."""

    def __init__(self, setup, record):
        self.setup, self.record = setup, record
        self._prices: Optional[Dict[str, float]] = None
        self._costs: Optional[Dict[str, float]] = None
        self._ceilings: Dict[str, AskCeiling] = {}
        self._multiples: Dict[tuple, float] = {}

    def _read(self) -> None:
        if self._prices is None:
            from .national_prices import national_prices
            from .notional import making_costs
            self._prices, self._costs = national_prices(self.record), making_costs(self.setup, self.record)

    def _price(self, good: str) -> Optional[float]:
        self._read()
        return self._prices.get(good)

    def _cost(self, good: str) -> Optional[float]:
        self._read()
        return self._costs.get(good)

    def ceiling(self, good: str, tile: str) -> AskCeiling:
        """The good's `alternative_ceiling` for the people of `tile` (prices are read only for a good that meets a need)."""
        key = (good, tile)
        found = self._ceilings.get(key)
        if found is None:
            found = self._ceilings[key] = alternative_ceiling(good, self.setup.basket_for(tile).needs, self._price, self._cost)
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
