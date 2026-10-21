"""What the markets remember between years, and the read-only view agents plan from.

Prices, wages and rates are last year's outcomes; holdings are now. An agent planning this year
sees nothing of this year's clearing, which is where the economy's lags come from.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional

from sim.constants import declare

from .accounts import Book
from .currency import update_expected_inflation
from .types import QUOTE_OPENING_ESTIMATE, AgentId, AreaId, CurrencyId, GoodId, TileId, TradeId

KEY_SEPARATOR = "|"
PRICE_TRADED = "traded"     # the kind of a price a market cleared at; any other kind is a quote or an estimate

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

USUAL_PRICE_SPEED = declare(
    "USUAL_PRICE_SPEED", 0.1, kind="temporary_heuristic",
    unit="share of the gap to this year's price closed in a year", source=None, confidence="D",
    why="Holders of a durable good judge a price high or low against what it has usually been. How long "
        "'usually' is has no measured basis; a moving average over about a decade is the same idea.")


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
    basket_price_levels: Dict[CurrencyId, float] = field(default_factory=dict)
    expected_inflation: Dict[CurrencyId, float] = field(default_factory=dict)
    observed_inflation: Dict[CurrencyId, float] = field(default_factory=dict)   # last year's, the weighted median of price changes
    last_year_prices: Dict[str, float] = field(default_factory=dict)    # good: national price the year before, for that median
    currency_of_area: Dict[AreaId, CurrencyId] = field(default_factory=dict)
    usual_prices: Dict[str, float] = field(default_factory=dict)        # market_key(good, area), slow average
    volume_weights: Dict[str, float] = field(default_factory=dict)      # market_key(good, area), smoothed
    trade_age: Dict[str, int] = field(default_factory=dict)     # market_key(good, area); absent: never cleared
    years_without_bids: Dict[str, int] = field(default_factory=dict)   # market_key(good, area); absent: bids last year
    years_without_offers: Dict[str, int] = field(default_factory=dict)   # market_key(good, area); absent: offers last year
    cleared_prices: Dict[str, float] = field(default_factory=dict)      # market_key(good, area); absent: nothing traded last year
    quote_kinds: Dict[str, str] = field(default_factory=dict)           # market_key(good, area); what `prices` holds when nothing traded

    def price_kind(self, key: str) -> Optional[str]:
        """What the price remembered for a market is: PRICE_TRADED when it traded last year, else the quote's
        kind, else the opening estimate no clearing has replaced; None when the market has no price."""
        if key in self.cleared_prices:
            return PRICE_TRADED
        if key not in self.prices:
            return None
        return self.quote_kinds.get(key, QUOTE_OPENING_ESTIMATE)

    def price_kinds_by_good(self) -> Dict[str, str]:
        """The kind each good's price has across its markets: traded when any market of it traded last year,
        else the first quote kind in market order (so a price no one traded at is never shown as a trade)."""
        kinds: Dict[str, str] = {}
        for key in sorted(self.prices):
            good = key.split(KEY_SEPARATOR, 1)[0]
            kind = self.price_kind(key)
            if kinds.get(good) != PRICE_TRADED and (kind == PRICE_TRADED or good not in kinds):
                kinds[good] = kind
        return kinds

    def note_cleared(self, key: str, price: float, quantity: float) -> None:
        """Keep the price a market cleared at when it traded; forget it when it did not."""
        if quantity > 0.0 and price > 0.0:
            self.cleared_prices[key] = price
        else:
            self.cleared_prices.pop(key, None)

    def note_usual_price(self, key: str) -> None:
        """Move the usual price of a market toward its remembered price (start at it when new)."""
        price = self.prices.get(key)
        if price is None:
            return
        usual = self.usual_prices.get(key)
        self.usual_prices[key] = price if usual is None else usual + USUAL_PRICE_SPEED * (price - usual)

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

    def note_basket_price_level(self, currency: CurrencyId, level: float, observed_inflation: Optional[float] = None) -> None:
        """Record this year's price level and move the expectation of inflation after the year's observed inflation
        (the weighted median of the goods' price changes when the caller has it, else the change in the level)."""
        previous = self.basket_price_levels.get(currency)
        if observed_inflation is None and previous and previous > 0.0:
            observed_inflation = level / previous - 1.0
        if observed_inflation is not None:
            expected = self.expected_inflation.get(currency, OPENING_EXPECTED_INFLATION)
            self.expected_inflation[currency] = update_expected_inflation(expected, observed_inflation)
            self.observed_inflation[currency] = observed_inflation
        self.basket_price_levels[currency] = level


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
        self._keys_of_good: Dict[str, tuple] = {}
        self._keys_at_tile: Dict[str, tuple] = {}
        self._keys_of_names: Dict[tuple, tuple] = {}     # (id of a names tuple, wages) -> (names, tile -> market keys)
        self._area_by_tile: Dict[str, Dict[TileId, AreaId]] = {}    # name -> tile -> its area; the area map does not change

    def prices_across(self, good: GoodId, areas) -> list:
        """`price(good, area.area_id)` for each of `areas` (the good's areas), in order."""
        keys = self._keys_of_good.get(good)
        if keys is None or keys[0] is not areas:
            keys = self._keys_of_good[good] = (areas, [good + KEY_SEPARATOR + area.area_id for area in areas])
        prices = self._memory.prices
        return list(map(prices.get, keys[1]))

    def price_rows(self, goods, tile: TileId) -> list:
        """(good, price, usual price) for each of `goods` in the market area it trades in on `tile`."""
        keys = self._keys_at_tile.get(tile)
        if keys is None or keys[0] is not goods:
            keys = self._keys_at_tile[tile] = (goods, [(good, good + KEY_SEPARATOR + self.area_of(good, tile))
                                                        for good in goods])
        prices, usual_prices = self._memory.prices, self._memory.usual_prices
        return [(good, prices.get(key), usual_prices.get(key)) for good, key in keys[1]]

    def price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """The planning price: last year's traded price, or, where nothing traded, the quote (`quote_kind`
        says which). A reader that needs a price both sides agreed to uses `cleared_price`."""
        return self._memory.prices.get(good + KEY_SEPARATOR + area)

    def present_prices_at(self, names: tuple, tile: TileId, wages: bool = False) -> Dict[str, float]:
        """`price` (or `wage` when `wages`) of each of `names` (goods or trades, one tuple kept by the caller) in its
        area on `tile`, those with a figure only, in order: the keys are built once per names tuple and tile."""
        kept = self._keys_of_names.get((id(names), wages))
        if kept is None or kept[0] is not names:
            kept = self._keys_of_names[(id(names), wages)] = (names, {})
        keys = kept[1].get(tile)
        if keys is None:
            keys = kept[1][tile] = tuple(name + KEY_SEPARATOR + self.area_of(name, tile) for name in names)
        table = self._memory.wages if wages else self._memory.prices
        found = {}
        for name, key in zip(names, keys):
            figure = table.get(key)
            if figure is not None:
                found[name] = figure
        return found

    def quote_kind(self, good: GoodId, area: AreaId) -> Optional[str]:
        """What `price` is when nothing traded last year (a QUOTE_* kind); None when it is a traded price or
        the opening estimate no market has replaced (`price_kind` names those too)."""
        return self._memory.quote_kinds.get(good + KEY_SEPARATOR + area)

    def price_kind(self, good: GoodId, area: AreaId) -> Optional[str]:
        """PRICE_TRADED, or the kind of quote or estimate `price` is; None when the market has no price."""
        return self._memory.price_kind(good + KEY_SEPARATOR + area)

    def cleared_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """The price the market cleared at last year; None when nothing traded in it."""
        return self._memory.cleared_prices.get(good + KEY_SEPARATOR + area)

    def usual_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """A slow average of the price, what holders compare today's price with; None before any."""
        return self._memory.usual_prices.get(good + KEY_SEPARATOR + area)

    def wage(self, trade: TradeId, area: AreaId) -> Optional[float]:
        return self._memory.wages.get(trade + KEY_SEPARATOR + area)

    def interest_rate(self, currency: CurrencyId) -> float:
        return self._memory.rates.get(currency, 0.0)

    def area_of(self, good_or_trade: str, tile: TileId) -> AreaId:
        """A good's market area on this tile; a trade's labour area when the key is not a good."""
        by_tile = self._area_by_tile.get(good_or_trade)
        if by_tile is None:
            by_tile = self._area_by_tile[good_or_trade] = {}
        area = by_tile.get(tile)
        if area is None:
            area = by_tile[tile] = (self._area_map.area_of(good_or_trade, tile) if good_or_trade in self._goods
                                    else self._labour_area_of(tile))
        return area

    def currency_of(self, area: AreaId) -> CurrencyId:
        return self._memory.currency_of_area.get(area, self._currency)

    def basket_price_level(self, currency: CurrencyId) -> float:
        return self._memory.basket_price_levels.get(currency, 1.0)

    def expected_inflation(self, currency: CurrencyId) -> float:
        return self._memory.expected_inflation.get(currency, OPENING_EXPECTED_INFLATION)

    def observed_inflation(self, currency: CurrencyId) -> Optional[float]:
        return self._memory.observed_inflation.get(currency)

    def cash(self, agent: AgentId, currency: CurrencyId) -> float:
        return self._book.balance(agent, currency)

    def stock(self, agent: AgentId, good: GoodId, tile: TileId) -> float:
        return self._book.stock(agent, good, tile)
