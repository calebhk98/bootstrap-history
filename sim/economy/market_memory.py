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

VOLUME_WEIGHT_SPEED = declare(
    "VOLUME_WEIGHT_SPEED", 0.3, kind="temporary_heuristic",
    unit="share of the gap to this year's volume closed in a year", source=None, confidence="D",
    why="A national price weights each market area by what it usually trades, so trade that moves "
        "between areas from year to year does not swing it. How long 'usually' is has no measured "
        "basis; a fixed-basket index with weights from earlier years is the same idea.")


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
    volume_weights: Dict[str, float] = field(default_factory=dict)      # market_key(good, area), smoothed
    trade_age: Dict[str, int] = field(default_factory=dict)     # market_key(good, area); absent: never cleared

    def years_since_trade(self, key: str) -> Optional[int]:
        return self.trade_age.get(key)

    def note_trading(self, traded_keys) -> None:
        """A year ends: the markets that cleared are current, the rest are a year older. A market that
        has never cleared has no age; its remembered price is an opening estimate, not a market's."""
        for key in list(self.trade_age):
            self.trade_age[key] += 1
        for key in traded_keys:
            self.trade_age[key] = 0

    def note_volume(self, key: str, quantity: float) -> None:
        """Move a market's usual volume toward what it traded this year."""
        old = self.volume_weights.get(key)
        self.volume_weights[key] = quantity if old is None else old + VOLUME_WEIGHT_SPEED * (quantity - old)

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

    def __init__(self, memory: MarketMemory, book: Book, area_map, currency: CurrencyId,
                 labour_area_of=None) -> None:
        self.year = memory.year + 1
        self._memory = memory
        self._book = book
        self._area_map = area_map
        self._currency = currency
        self._labour_area_of = labour_area_of
        self._goods = set(area_map.goods())

    def price(self, good: GoodId, area: AreaId) -> Optional[float]:
        return self._memory.prices.get(market_key(good, area))

    def wage(self, trade: TradeId, area: AreaId) -> Optional[float]:
        return self._memory.wages.get(market_key(trade, area))

    def interest_rate(self, currency: CurrencyId) -> float:
        return self._memory.rates.get(currency, 0.0)

    def area_of(self, good_or_trade: str, tile: TileId) -> AreaId:
        """A good's market area on this tile; a trade's labour area when the key is not a good."""
        if good_or_trade in self._goods:
            return self._area_map.area_of(good_or_trade, tile)
        return self._labour_area_of(tile)

    def currency_of(self, area: AreaId) -> CurrencyId:
        return self._memory.currency_of_area.get(area, self._currency)

    def price_level(self, currency: CurrencyId) -> float:
        return self._memory.price_levels.get(currency, 1.0)

    def expected_inflation(self, currency: CurrencyId) -> float:
        return self._memory.expected_inflation.get(currency, OPENING_EXPECTED_INFLATION)

    def cash(self, agent: AgentId, currency: CurrencyId) -> float:
        return self._book.balance(agent, currency)

    def stock(self, agent: AgentId, good: GoodId, tile: TileId) -> float:
        return self._book.stock(agent, good, tile)
