"""What the markets remember between years, and the read-only view agents plan from.

Prices, wages and rates are last year's outcomes; holdings are now. An agent planning this year
sees nothing of this year's clearing, which is where the economy's lags come from.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional

from sim.constants import declare

from .accounts import Book
from .currency import update_expected_inflation
from .types import AgentId, AreaId, CurrencyId, GoodId, TileId, TradeId

KEY_SEPARATOR = "|"

OPENING_EXPECTED_INFLATION = declare(
    "OPENING_EXPECTED_INFLATION", 0.0, kind="initial_condition",
    unit="share per year", source=None, confidence="C",
    why="At the opening nobody has seen prices move, so the expectation agents start from is no "
        "change; adaptive expectations then follow what the price level does.")


def market_key(first: str, area: AreaId) -> str:
    """One string key per (good or trade, area), so the memory saves as plain JSON."""
    return first + KEY_SEPARATOR + area


@dataclass
class MarketMemory:
    """Last year's outcomes, saved with the game."""
    year: int = 0
    prices: Dict[str, float] = field(default_factory=dict)              # market_key(good, area)
    wages: Dict[str, float] = field(default_factory=dict)               # market_key(trade, area)
    rates: Dict[CurrencyId, float] = field(default_factory=dict)
    price_levels: Dict[CurrencyId, float] = field(default_factory=dict)
    expected_inflation: Dict[CurrencyId, float] = field(default_factory=dict)
    currency_of_area: Dict[AreaId, CurrencyId] = field(default_factory=dict)

    def note_price_level(self, currency: CurrencyId, level: float) -> None:
        """Record this year's price level and move the expectation of inflation after it."""
        previous = self.price_levels.get(currency)
        if previous and previous > 0.0:
            observed = level / previous - 1.0
            expected = self.expected_inflation.get(currency, OPENING_EXPECTED_INFLATION)
            self.expected_inflation[currency] = update_expected_inflation(expected, observed)
        self.price_levels[currency] = level


class YearView:
    """`protocols.MarketView` over the memory, the book and the area map, for one year's planning."""

    def __init__(self, memory: MarketMemory, book: Book, area_map) -> None:
        self.year = memory.year + 1
        self._memory = memory
        self._book = book
        self._area_map = area_map

    def price(self, good: GoodId, area: AreaId) -> Optional[float]:
        return self._memory.prices.get(market_key(good, area))

    def wage(self, trade: TradeId, area: AreaId) -> Optional[float]:
        return self._memory.wages.get(market_key(trade, area))

    def interest_rate(self, currency: CurrencyId) -> float:
        return self._memory.rates.get(currency, 0.0)

    def area_of(self, good: GoodId, tile: TileId) -> AreaId:
        return self._area_map.area_of(good, tile)

    def currency_of(self, area: AreaId) -> CurrencyId:
        return self._memory.currency_of_area[area]

    def price_level(self, currency: CurrencyId) -> float:
        return self._memory.price_levels.get(currency, 1.0)

    def expected_inflation(self, currency: CurrencyId) -> float:
        return self._memory.expected_inflation.get(currency, OPENING_EXPECTED_INFLATION)

    def cash(self, agent: AgentId, currency: CurrencyId) -> float:
        return self._book.balance(agent, currency)

    def stock(self, agent: AgentId, good: GoodId, tile: TileId) -> float:
        return self._book.stock(agent, good, tile)
