"""What the markets remember between years, and the read-only view agents plan from.

Prices, wages and rates are last year's outcomes; holdings are now. An agent planning this year
sees nothing of this year's clearing, which is where the economy's lags come from.
"""
from dataclasses import dataclass, field, fields
from typing import Any, ClassVar, Dict, Optional, Tuple

import numpy as np

from sim.constants import declare

from sim.book import Book
from .currency import update_expected_inflation
from .market_arrays import FLOAT, INTEGER, KEY_SEPARATOR, TEXT, MarketIds, MarketStore
from .record_plain import plain
from .types import QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE, AgentId, AreaId, CurrencyId, GoodId, TileId, TradeId

PRICE_LEVEL_FLOOR_RATIO = 1e-9   # a year in which the median price fell to nothing still leaves a positive level to chain from
PRICE_SMOOTHED_TRADE = "smoothed_trade"     # the kind of the price remembered for a market that traded: the old price moved toward the clearing price; any other kind is a quote or an estimate
PRICE_REMEMBERED = "remembered_price"   # a price from a trade of some earlier year that nothing since has replaced or quoted

_writes = [0]      # bumped by each write to the prices, wages, rates and price levels a view's cached reads come from


def note_written() -> None:
    _writes[0] += 1


def written_stamp() -> int:
    """Changes with every write to the prices, wages, rates, quotes and trade ages a reader's copy comes from."""
    return _writes[0]


OPENING_EXPECTED_INFLATION = declare(
    "OPENING_EXPECTED_INFLATION", 0.0, kind="initial_condition",
    unit="share per year", source=None, confidence="C",
    why="At the opening nobody has seen prices move, so the expectation agents start from is no "
        "change; adaptive expectations then follow what the price level does.")

RECENT_TRADE_YEARS = declare(
    "RECENT_TRADE_YEARS", 2, kind="temporary_heuristic",
    unit="years since a market last cleared", source=None, confidence="D",
    why="A good's price counts as a market price, and counts in the price index, only while one of its "
        "markets cleared within this many years. A thin market trades in alternate years, so one year "
        "would drop it too eagerly; how long a gap makes a price stale has no measured basis.")

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
    OWNERS: ClassVar[Tuple[str, ...]] = ("market_memory",)   # the sim/economy modules allowed to write this (tools/check_record_owners.py)
    GOODS_MARKET_KEYED: ClassVar[Tuple[str, ...]] = ("prices", "usual_prices", "volume_weights", "trade_age", "years_without_bids",
                                                     "years_without_offers", "cleared_prices", "quote_kinds")   # the stores keyed by market_key(good, area): they move when the areas are redrawn
    STORES: ClassVar[Dict[str, Tuple[str, str]]] = {   # the market-keyed stores: name -> (which numbering, the kind of figure); each is a `MarketStore` (market_arrays.py)
        "prices": ("goods", FLOAT), "wages": ("trades", FLOAT), "usual_prices": ("goods", FLOAT), "volume_weights": ("goods", FLOAT),
        "trade_age": ("goods", INTEGER), "years_without_bids": ("goods", INTEGER), "years_without_offers": ("goods", INTEGER),
        "cleared_prices": ("goods", FLOAT), "quote_kinds": ("goods", TEXT)}
    year: int = 0
    prices: Dict[str, float] = field(default_factory=dict)              # market_key(good, area)
    wages: Dict[str, float] = field(default_factory=dict)               # market_key(trade, area)
    rates: Dict[CurrencyId, float] = field(default_factory=dict)
    basket_price_levels: Dict[CurrencyId, float] = field(default_factory=dict)
    expected_inflation: Dict[CurrencyId, float] = field(default_factory=dict)
    price_levels: Dict[CurrencyId, float] = field(default_factory=dict)   # the opening's level (1.0) chained by each year's observed inflation (the weighted median): what real figures are turned nominal with
    opening_wage_levels: Dict[CurrencyId, float] = field(default_factory=dict)   # the price level the setup's opening wages stand at: the product of the chained levels each rebase reset (absent: 1.0)
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

    def __setattr__(self, name: str, value: Any) -> None:
        """A market-keyed store is held as arrays: a mapping assigned to one is read into a `MarketStore` on this memory's numbering."""
        spec = self.STORES.get(name)
        if spec is not None:
            ids = self.numbering(spec[0])
            if not (isinstance(value, MarketStore) and value.ids is ids and value.kind == spec[1]):
                value = MarketStore(ids, spec[1], value.items() if hasattr(value, "items") else value)
        object.__setattr__(self, name, value)

    def numbering(self, which: str) -> MarketIds:
        """The goods' (or the trades') numbering the stores share: ids are given once, in the order markets are first met."""
        name = "_ids_of_" + which
        ids = self.__dict__.get(name)
        if ids is None:
            ids = self.__dict__[name] = MarketIds()
        return ids

    def to_record(self) -> Dict[str, Any]:
        """The memory as plain data: a field each, the market-keyed stores as {market key: figure} in key order."""
        saved = {}
        for each in fields(self):
            value = getattr(self, each.name)
            saved[each.name] = value.copy_dict() if isinstance(value, MarketStore) else plain(value)
        return saved

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "MarketMemory":
        return cls(**record)

    def cell_of(self, good: str, area: str) -> Optional[Tuple[int, int]]:
        """The (row, column) of a goods market in the goods' arrays; None for a market the memory has never held."""
        by_area = self.numbering("goods").cell_of_pair.get(good)
        return None if by_area is None else by_area.get(area)

    def advance_year(self) -> None:
        self.year += 1

    def reset_year(self) -> None:
        self.year = 0

    def set_rate(self, money: CurrencyId, rate: float) -> None:
        self.rates[money] = rate
        note_written()

    def set_price(self, key: str, price: float) -> None:
        self.prices[key] = price
        note_written()

    def count_year_without_bids(self, key: str) -> int:
        """A market with offers had nobody bidding this year; returns the years it had gone before."""
        before = self.years_without_bids.get(key, 0)
        self.years_without_bids[key] = before + 1
        return before

    def end_years_without_bids(self, key: str) -> int:
        """Bids came (or there was nothing to bid on); returns the years without that had gone before."""
        return self.years_without_bids.pop(key, 0)

    def count_year_without_offers(self, key: str) -> int:
        """A market with bids had no seller this year; returns the years it had gone before."""
        before = self.years_without_offers.get(key, 0)
        self.years_without_offers[key] = before + 1
        return before

    def end_years_without_offers(self, key: str) -> int:
        """Sellers came (or nobody was bidding); returns the years without that had gone before."""
        return self.years_without_offers.pop(key, 0)

    def set_quote_kind(self, key: str, kind: str) -> None:
        self.quote_kinds[key] = kind
        note_written()

    def drop_quote_kind(self, key: str) -> None:
        self.quote_kinds.pop(key, None)
        note_written()

    def set_area_currencies(self, currency_of_area: Dict[AreaId, CurrencyId]) -> None:
        self.currency_of_area = currency_of_area

    def set_last_year_prices(self, prices: Dict[str, float]) -> None:
        self.last_year_prices = dict(prices)

    def rebase_price_levels(self, money: CurrencyId) -> None:
        """The price level of `money` is one, both the basket's and the chained one. The setup's opening wages stay in
        opening-year money, so the chained level being reset moves into `opening_wage_levels`."""
        self.opening_wage_levels[money] = self.opening_wage_level(money)
        self.basket_price_levels[money] = 1.0
        self.price_levels[money] = 1.0
        note_written()

    def holds_wage_for(self, trade: TradeId) -> bool:
        """Whether the memory holds a wage for the trade in any labour area (a trade the core has never cleared, such as one
        admitted after the opening, has none)."""
        row = self.numbering("trades").first_row.get(trade)
        if row is None or row >= self.wages.grid.shape[0]:
            return False
        return not bool(np.isnan(self.wages.grid[row]).all())

    def opening_wage_level(self, money: CurrencyId) -> float:
        """Today's money per opening-year money for a wage the setup holds: the level before the last rebase times the
        chained level since."""
        return self.opening_wage_levels.get(money, 1.0) * self.price_levels.get(money, 1.0)

    def price_kind(self, key: str) -> Optional[str]:
        """What the price remembered for a market is: PRICE_SMOOTHED_TRADE when it traded last year, else the quote's
        kind, else the opening estimate no clearing has replaced; None when the market has no price."""
        cell = self.numbering("goods").cells.get(key)
        return None if cell is None else self.price_kind_at(cell)

    def price_kind_at(self, cell: Tuple[int, int]) -> Optional[str]:
        """`price_kind` of the market in a cell of the goods' arrays."""
        age = self.trade_age.read_cell(cell)
        if age is not None and age <= 0:
            return PRICE_SMOOTHED_TRADE
        if self.prices.read_cell(cell) is None:
            return None
        kind = self.quote_kinds.read_cell(cell)
        if kind is not None:
            return kind
        return PRICE_REMEMBERED if age is not None else QUOTE_OPENING_ESTIMATE

    def offered_price(self, key: str) -> Optional[float]:
        """What a buyer can see to buy at: a price the market traded at, an ask still posted, or the opening's own
        estimate before any clearing; None for a bid ceiling, a cost quote or a price remembered from an old trade
        (nothing is on offer at those). Eurace's consumers see the mall's current prices and the quality of the goods
        (the logit weighs both; Cons_Goods/Household_Consumer_Functions.c), nothing remembered (Complaint 642); this
        model has the price only."""
        cell = self.numbering("goods").cells.get(key)
        return None if cell is None else self.offered_price_at(cell)

    def offered_price_at(self, cell: Tuple[int, int]) -> Optional[float]:
        """`offered_price` of the market in a cell of the goods' arrays."""
        if self.price_kind_at(cell) in (PRICE_SMOOTHED_TRADE, QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE):
            return self.prices.read_cell(cell)
        return None

    def price_kinds_by_good(self) -> Dict[str, str]:
        """The kind each good's price has across its markets: traded when any market of it traded last year,
        else the first quote kind in market order (so a price no one traded at is never shown as a trade). Worked on the arrays:
        the priced markets in key order, their age and quote, then one kind per good."""
        keys, rows, columns = self.prices.positions()
        if not keys:
            return {}
        age = self.trade_age.at(rows, columns)
        quote = self.quote_kinds.at(rows, columns)
        kinds = np.where(age >= 0, PRICE_REMEMBERED, QUOTE_OPENING_ESTIMATE).astype(object)
        words = np.array(self.quote_kinds.words, dtype=object)
        quoted = quote >= 0
        kinds[quoted] = words[quote[quoted]]
        traded = (age >= 0) & (age <= 0)
        kinds[traded] = PRICE_SMOOTHED_TRADE
        starts = np.flatnonzero(np.concatenate(([True], rows[1:] != rows[:-1])))
        any_traded = np.add.reduceat(traded.astype(np.int64), starts) > 0
        names = self.numbering("goods").first_names
        return {names[row]: (PRICE_SMOOTHED_TRADE if hit else kind)
                for row, hit, kind in zip(rows[starts].tolist(), any_traded.tolist(), kinds[starts].tolist())}

    def note_cleared(self, key: str, price: Optional[float], quantity: float) -> None:
        """Keep the price a market cleared at when it traded; forget it when it did not."""
        if quantity > 0.0 and price is not None and price > 0.0:
            self.cleared_prices[key] = price
        else:
            self.cleared_prices.pop(key, None)
        note_written()

    def note_usual_price(self, key: str) -> None:
        """Move the usual price of a market toward its remembered price (start at it when new)."""
        price = self.prices.get(key)
        if price is None:
            return
        usual = self.usual_prices.get(key)
        self.usual_prices[key] = price if usual is None else usual + USUAL_PRICE_SPEED * (price - usual)

    def traded_within(self, key: str, years: int) -> bool:
        """The one meaning of "traded": the market cleared at most `years` years ago (0: last year). A market that
        never cleared, whatever estimate or quote its price is, has not traded."""
        age = self.trade_age.get(key)
        return age is not None and age <= years

    def note_trading(self, traded_keys) -> None:
        """A year ends: the markets that cleared are current, the rest are a year older. A market that
        has never cleared has no age; its remembered price is an opening estimate, not a market's."""
        self.trade_age.add_to_all(1)
        for key in traded_keys:
            self.trade_age[key] = 0
        note_written()

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
            before = self.price_levels.get(currency, 1.0)
            self.price_levels[currency] = before * max(PRICE_LEVEL_FLOOR_RATIO, 1.0 + observed_inflation)
        self.basket_price_levels[currency] = level
        note_written()


from .market_view import YearView   # noqa: E402,F401  (the view over the memory lives in market_view.py)
