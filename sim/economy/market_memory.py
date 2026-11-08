"""What the markets remember between years, and the read-only view agents plan from.

Prices, wages and rates are last year's outcomes; holdings are now. An agent planning this year
sees nothing of this year's clearing, which is where the economy's lags come from.
"""
import dataclasses
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Optional, Set, Tuple

import numpy

from sim.constants import declare

from sim.book import Book
from .currency import update_expected_inflation
from .market_store import CountStore, FloatStore, KindStore, MarketStore, labour_wage_store
from .market_table_kernels import markets_traded_within, note_year_traded
from .market_table_specs import (CLEARED_PRICES, HELD_QUOTE_KIND, HELD_TRADE_AGE, HELD_YEARS_WITHOUT_BIDS, HELD_YEARS_WITHOUT_OFFERS, KEY_SEPARATOR,
                                 PRICES, TRADE_AGE, USUAL_PRICES, VOLUME_WEIGHTS, YEARS_WITHOUT_BIDS, YEARS_WITHOUT_OFFERS)
from .market_tables import MarketTables
from .record_plain import plain
from .types import QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE, AgentId, AreaId, CurrencyId, GoodId, TileId, TradeId

PRICE_LEVEL_FLOOR_RATIO = 1e-9   # a year in which the median price fell to nothing still leaves a positive level to chain from
PRICE_SMOOTHED_TRADE = "smoothed_trade"     # the kind of the price remembered for a market that traded: the old price moved toward the clearing price; any other kind is a quote or an estimate
PRICE_REMEMBERED = "remembered_price"   # a price from a trade of some earlier year that nothing since has replaced or quoted

_OFFERED_QUOTE_KINDS = (QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE)    # the quote kinds a buyer can buy at

_writes = [0]      # bumped by each write to the prices, wages, rates and price levels a view's cached reads come from
_age_and_kind_writes = [0]      # bumped by each in-place write to the trade ages and quote kinds (a redraw replaces the stores whole)


def note_written() -> None:
    _writes[0] += 1


def age_and_kind_stamp() -> int:
    """Changes with every in-place write to the trade ages and quote kinds, and to nothing else."""
    return _age_and_kind_writes[0]


def note_age_and_kind_written() -> None:
    """The trade ages and quote kinds were replaced whole (an area redraw): drop what was kept from them."""
    _age_and_kind_writes[0] += 1
    note_written()


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




STORE_NAMES = ("prices", "usual_prices", "cleared_prices", "volume_weights", "trade_age", "years_without_bids",
               "years_without_offers", "quote_kinds", "wages")    # the fields that are views of the market tables (`market_store.py`)


def make_stores(tables: MarketTables) -> Dict[str, MarketStore]:
    """One store per name in STORE_NAMES, each a view of a column of `tables`."""
    return {
        "prices": FloatStore(tables, PRICES, "price"), "usual_prices": FloatStore(tables, USUAL_PRICES, "usual_price"),
        "cleared_prices": FloatStore(tables, CLEARED_PRICES, "cleared_price"),
        "volume_weights": FloatStore(tables, VOLUME_WEIGHTS, "volume_weight"),
        "trade_age": CountStore(tables, TRADE_AGE, "trade_age", HELD_TRADE_AGE),
        "years_without_bids": CountStore(tables, YEARS_WITHOUT_BIDS, "years_without_bids", HELD_YEARS_WITHOUT_BIDS),
        "years_without_offers": CountStore(tables, YEARS_WITHOUT_OFFERS, "years_without_offers", HELD_YEARS_WITHOUT_OFFERS),
        "quote_kinds": KindStore(tables), "wages": labour_wage_store(tables)}


def market_key(first: str, area: AreaId) -> str:
    """One string key per (good or trade, area), so the memory saves as plain JSON."""
    return first + KEY_SEPARATOR + area


@dataclass
class MarketMemory:
    """Last year's outcomes, saved with the game."""
    OWNERS: ClassVar[Tuple[str, ...]] = ("market_memory",)   # the sim/economy modules allowed to write this (tools/check_record_owners.py)
    GOODS_MARKET_KEYED: ClassVar[Tuple[str, ...]] = ("prices", "usual_prices", "volume_weights", "trade_age", "years_without_bids",
                                                     "years_without_offers", "cleared_prices", "quote_kinds")   # the stores keyed by market_key(good, area): they move when the areas are redrawn
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

    def __post_init__(self) -> None:
        given = {name: self.__dict__[name] for name in STORE_NAMES}     # the dicts the constructor was handed
        self.__dict__["tables"] = MarketTables()
        self.__dict__.update(make_stores(self.tables))
        for name, figures in given.items():
            self._load_store(name, figures)

    def __setattr__(self, name, value) -> None:
        if name in STORE_NAMES and "tables" in self.__dict__:
            if value is not self.__dict__[name]:
                self._load_store(name, value)
                note_written()
                if name in ("trade_age", "quote_kinds"):
                    _age_and_kind_writes[0] += 1
        else:
            object.__setattr__(self, name, value)

    def _load_store(self, name: str, figures) -> None:
        """Make the store hold exactly `figures` (a mapping by market key), in its order; new markets are numbered first as one batch."""
        if name == "wages":
            self.tables.admit_labour_markets(figures)
        else:
            self.tables.admit_goods_markets(figures)
        self.__dict__[name].replace_with(figures)

    def to_plain(self) -> Dict[str, object]:
        """The memory as plain data for a save: the stores as dicts in their order, and the market numberings."""
        saved: Dict[str, object] = {}
        for each in dataclasses.fields(self):
            value = getattr(self, each.name)
            saved[each.name] = dict(value.items()) if isinstance(value, MarketStore) else plain(value)
        saved["market_ids"] = self.tables.state()
        return saved

    @classmethod
    def from_plain(cls, saved: Dict[str, object]) -> "MarketMemory":
        """The memory a save stored: the numberings first, so the markets have the numbers they had, then the stores."""
        saved = dict(saved)
        numbering = saved.pop("market_ids", None)
        figures = {name: saved.pop(name, {}) for name in STORE_NAMES}
        memory = cls(**saved)
        memory.tables.load_state(numbering)
        for name, each in figures.items():
            memory._load_store(name, each)
        return memory

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
        _age_and_kind_writes[0] += 1
        note_written()

    def drop_quote_kind(self, key: str) -> None:
        self.quote_kinds.pop(key, None)
        _age_and_kind_writes[0] += 1
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
        stamp = (_writes[0], len(self.wages))
        kept = self.__dict__.get("_wage_trades")     # not a field: a read kept until the wages are written to
        if kept is None or kept[0] != stamp:
            kept = self.__dict__["_wage_trades"] = (stamp, self._trades_with_a_wage())
        return trade in kept[1]

    def _trades_with_a_wage(self) -> frozenset:
        labour = self.tables.labour_table
        rows = ~numpy.isnan(labour.wage[:labour.row_count[0]])
        names = self.tables.trades.names
        return frozenset(names[number] for number in numpy.unique(labour.first[:labour.row_count[0]][rows]).tolist())

    def opening_wage_level(self, money: CurrencyId) -> float:
        """Today's money per opening-year money for a wage the setup holds: the level before the last rebase times the
        chained level since."""
        return self.opening_wage_levels.get(money, 1.0) * self.price_levels.get(money, 1.0)

    def price_kind(self, key: str) -> Optional[str]:
        """What the price remembered for a market is: PRICE_SMOOTHED_TRADE when it traded last year, else the quote's
        kind, else the opening estimate no clearing has replaced; None when the market has no price."""
        row = self.tables.goods_numbers.get(key)
        if row is None:
            return None
        markets = self.tables.goods_table
        held = markets.held.item(row)
        if held & HELD_TRADE_AGE and markets.trade_age.item(row) <= 0:
            return PRICE_SMOOTHED_TRADE
        price = markets.price.item(row)
        if price != price:
            return None
        if held & HELD_QUOTE_KIND:
            return self.tables.kinds.name(markets.quote_kind.item(row))
        return PRICE_REMEMBERED if held & HELD_TRADE_AGE else QUOTE_OPENING_ESTIMATE

    def offered_price(self, key: str) -> Optional[float]:
        """What a buyer can see to buy at: a price the market traded at, an ask still posted, or the opening's own
        estimate before any clearing; None for a bid ceiling, a cost quote or a price remembered from an old trade
        (nothing is on offer at those). Eurace's consumers see the mall's current prices and the quality of the goods
        (the logit weighs both; Cons_Goods/Household_Consumer_Functions.c), nothing remembered (Complaint 642); this
        model has the price only."""
        row = self.tables.goods_numbers.get(key)
        if row is None:
            return None
        markets = self.tables.goods_table
        price = markets.price.item(row)
        if price != price:
            return None
        held = markets.held.item(row)
        if held & HELD_TRADE_AGE and markets.trade_age.item(row) <= 0:
            return price
        if held & HELD_QUOTE_KIND:
            return price if self.tables.kinds.name(markets.quote_kind.item(row)) in _OFFERED_QUOTE_KINDS else None
        return None if held & HELD_TRADE_AGE else price     # a remembered price is nothing on offer; the opening's estimate is

    def _kept_read(self, name: str, compute):
        """`compute()` once per `name` until the memory is written to: the stamp is the write count and the identity and size
        of the stores a trade or a price kind is read from (an area redraw replaces them whole)."""
        stamp = (_writes[0], id(self.prices), len(self.prices), id(self.trade_age), len(self.trade_age),
                 id(self.quote_kinds), len(self.quote_kinds))
        kept = self.__dict__.setdefault("_kept_reads", {})     # not a field: reads kept until the stores are written to
        entry = kept.get(name)
        if entry is None or entry[0] != stamp:
            entry = kept[name] = (stamp, compute())
        return entry[1]

    def kept_for_ages_and_kinds(self, name: str, keys: tuple, compute):
        """`compute()` once per `name` and `keys` until a trade age or quote kind is written, or either store is replaced: a price
        written meanwhile does not drop it. The stores are held by the entry, so a replaced one is never mistaken for it."""
        stamp = _age_and_kind_writes[0]
        kept = self.__dict__.setdefault("_kept_ages_and_kinds", {})     # not a field
        entry = kept.get(name)
        if (entry is None or entry[0] != stamp or entry[1] is not self.trade_age or entry[2] is not self.quote_kinds
                or not (entry[3] is keys or entry[3] == keys)):
            entry = kept[name] = (stamp, self.trade_age, self.quote_kinds, keys, compute())
        return entry[4]

    def price_kinds_by_good(self) -> Dict[str, str]:
        """The kind each good's price has across its markets: traded when any market of it traded last year,
        else the first quote kind in market order (so a price no one traded at is never shown as a trade)."""
        return dict(self._kept_read("price_kinds", self._worked_out_price_kinds))

    def _worked_out_price_kinds(self) -> Dict[str, str]:
        kinds: Dict[str, str] = {}
        for key in sorted(self.prices):
            good = key.split(KEY_SEPARATOR, 1)[0]
            kind = self.price_kind(key)
            if kinds.get(good) != PRICE_SMOOTHED_TRADE and (kind == PRICE_SMOOTHED_TRADE or good not in kinds):
                kinds[good] = kind
        return kinds

    def goods_traded_within(self, years: int) -> Set[str]:
        """Goods with a market that cleared at most `years` years ago."""
        return set(self._kept_read(("traded_goods", years), lambda: self._goods_traded_within(years)))

    def _goods_traded_within(self, years: int) -> frozenset:
        markets = self.tables.goods_table
        traded = markets_traded_within(markets, years)
        names = self.tables.goods.names
        return frozenset(names[number] for number in numpy.unique(markets.first[:markets.row_count[0]][traded]).tolist())

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
        row = self.tables.goods_numbers.get(key)
        if row is None:
            return False
        markets = self.tables.goods_table
        return markets.held.item(row) & HELD_TRADE_AGE != 0 and markets.trade_age.item(row) <= years

    def note_trading(self, traded_keys) -> None:
        """A year ends: the markets that cleared are current, the rest are a year older. A market that
        has never cleared has no age; its remembered price is an opening estimate, not a market's."""
        rows = numpy.array([self.tables.goods_row_for_write(key) for key in traded_keys], dtype=numpy.int64)
        note_year_traded(self.tables.goods_table, rows, self.tables.next_order, self.tables.member_count)
        _age_and_kind_writes[0] += 1
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


class YearView:
    """`protocols.MarketView` over the memory, the book and the area map, for one year's planning."""

    def __init__(self, memory: MarketMemory, book: Book, area_map, currency: CurrencyId, setup,
                 labour_area_of=None) -> None:
        self.year = memory.year + 1
        self.setup = setup     # the trades and opening wages the wage rule (`trade_wages`) prices a trade from
        self._memory = memory
        self._book = book
        self._area_map = area_map
        self._currency = currency
        self._labour_area_of = labour_area_of
        self._goods = set(area_map.goods())
        self._keys_of_good: Dict[str, tuple] = {}
        self._area_by_tile: Dict[str, Dict[TileId, AreaId]] = {}    # name -> tile -> its area; the area map does not change
        self._stamp = _writes[0]
        self._reads: Dict[tuple, object] = {}     # reads of the memory kept until the next write to it
        self._offered: Dict[str, Optional[float]] = {}
        self._kinds: Dict[str, Optional[str]] = {}
        self._price_grid = None      # `price_grid.PriceGrid` over the memory, made on first use (False: the area map cannot be laid out)
        self._wage_table = None      # `wage_block.WageRuleTable`, likewise

    def prices_across(self, good: GoodId, areas) -> list:
        """`price(good, area.area_id)` for each of `areas` (the good's areas), in order."""
        keys = self._keys_of_good.get(good)
        if keys is None or keys[0] is not areas:
            keys = self._keys_of_good[good] = (areas, [good + KEY_SEPARATOR + area.area_id for area in areas])
        return self._memory.prices.get_many(keys[1], None)

    def price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """The planning price: the remembered price, last year's trade blended with the older price in proportion to
        the trade's share of the market's usual volume (`year_goods.remembered_price`), or, where nothing traded,
        the quote (`price_kind` says which); None where the market has no price. A reader that needs the price
        both sides agreed to last year uses `cleared_price`."""
        return self._memory.prices.get(good + KEY_SEPARATOR + area)

    def offered_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """What a buyer can buy at: the traded price or an ask still posted (`MarketMemory.offered_price`); None
        where nothing is on offer. A buyer reads this, never `price`."""
        if self._stamp != _writes[0]:
            self._current()
        key = good + KEY_SEPARATOR + area
        try:
            return self._offered[key]
        except KeyError:
            found = self._offered[key] = self._memory.offered_price(key)
            return found

    def _grid(self):
        """The offered-price grid of this view's memory and area map (False when the area map cannot list its goods and areas)."""
        if self._price_grid is None:
            from .price_grid import PriceGrid, price_index_of
            index = price_index_of(self._area_map)
            self._price_grid = False if index is None else PriceGrid(self._memory, index)
        return self._price_grid

    def offered_prices_on(self, tile: TileId):
        """The offered prices of every good on `tile` as one block (`price_grid.TilePrices`: `prices` of the goods that have one, `covered`
        the goods the block answers for), the same figures as `offered_price(good, area_of(good, tile))`; None for a tile the area map
        does not hold. Read again only after the memory is written to."""
        grid = self._grid()
        return grid.on_tile(tile) if grid else None

    def offered_prices_for(self, tile: TileId, goods) -> Dict[GoodId, Optional[float]]:
        """`offered_price(good, area_of(good, tile))` for each of `goods`, read from the tile's block; a good outside the block (the area
        map has no market for it) is read by itself."""
        block = self.offered_prices_on(tile)
        if block is None:
            return {good: self.offered_price(good, self.area_of(good, tile)) for good in goods}
        prices, covered = block.prices, block.covered
        return {good: prices.get(good) if good in covered else self.offered_price(good, self.area_of(good, tile)) for good in goods}

    def wage_rule_at(self, setup, trade: TradeId, area: AreaId) -> Optional[float]:
        """`trade_wages.wage_in_view` for one trade and labour area, read from the rule's table (every trade of the view's setup in the
        labour area of every tile of the area map); None where the table does not hold the cell or `setup` is not the view's."""
        if setup is not self.setup or self._labour_area_of is None:
            return None
        if self._wage_table is None:
            grid = self._grid()
            if not grid:
                self._wage_table = False
            else:
                from .wage_block import WageRuleTable
                tiles = grid.tiles
                self._wage_table = WageRuleTable(setup, self._memory, lambda: [self._labour_area_of(tile) for tile in tiles])
        return self._wage_table.wage(trade, area) if self._wage_table else None

    def wage_rule_block(self, trades, areas):
        """`trade_wages.wage_in_view` for each of `trades` in each of the labour `areas`, as a (trade by area) grid, in one kernel call."""
        from .wage_block import wage_rule_block
        return wage_rule_block(self.setup, self._memory, trades, areas)

    def remembered_prices_on(self, tile: TileId):
        """`offered_prices_on` for the remembered prices (`price`): every good that has one on `tile`, as one block."""
        grid = self._grid()
        return grid.on_tile(tile, remembered=True) if grid else None

    def present_prices_at(self, names: tuple, tile: TileId) -> Dict[str, float]:
        """`price` of each of `names` (goods, one tuple kept by the caller) in its area on `tile`, those with a
        price only, in order: read from the tile's block of remembered prices, once per names tuple and tile until the memory is written to."""
        reads = self._current()
        read_key = ("present", id(names), tile)
        kept_found = reads.get(read_key)
        if kept_found is None or kept_found[0] is not names:
            block = self.remembered_prices_on(tile)
            if block is not None and block.covers_all(names):
                found = {name: block.prices[name] for name in names if name in block.prices}
            else:
                found = self._present_prices_by_key(names, tile)
            kept_found = reads[read_key] = (names, found)
        return dict(kept_found[1])

    def _present_prices_by_key(self, names: tuple, tile: TileId) -> Dict[str, float]:
        """`present_prices_at` a good at a time, for a tile or goods outside the block."""
        found = {}
        for name in names:
            figure = self._memory.prices.get(name + KEY_SEPARATOR + self.area_of(name, tile))
            if figure is not None:
                found[name] = figure
        return found

    def price_kind(self, good: GoodId, area: AreaId) -> Optional[str]:
        """PRICE_SMOOTHED_TRADE, or the kind of quote or estimate `price` is; None when the market has no price."""
        if self._stamp != _writes[0]:
            self._current()
        key = good + KEY_SEPARATOR + area
        try:
            return self._kinds[key]
        except KeyError:
            found = self._kinds[key] = self._memory.price_kind(key)
            return found

    def cleared_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """The price the market cleared at last year; None when nothing traded in it."""
        return self._memory.cleared_prices.get(good + KEY_SEPARATOR + area)

    def usual_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """A slow average of the price, what holders compare today's price with; None before any."""
        return self._memory.usual_prices.get(good + KEY_SEPARATOR + area)

    def wage(self, trade: TradeId, area: AreaId) -> Optional[float]:
        return self._memory.wages.get(trade + KEY_SEPARATOR + area)

    def wage_held_anywhere(self, trade: TradeId) -> bool:
        """Whether the memory holds a wage for the trade in any area (`MarketMemory.holds_wage_for`)."""
        return self._memory.holds_wage_for(trade)

    def _current(self) -> Dict[tuple, object]:
        """The cached reads, dropped when the memory has been written to since they were made."""
        if self._stamp != _writes[0]:
            self._stamp = _writes[0]
            self._reads = {}
            self._offered = {}
            self._kinds = {}
        return self._reads

    def wages_at(self, trades: tuple, tile: TileId) -> Dict[str, float]:
        """The one wage rule (`trade_wages.wage_in_view`) for each of `trades` in its labour area on `tile`; read once per
        trades tuple (kept by the caller) and tile until the memory is written to."""
        from .trade_wages import wage_in_view
        reads = self._current()
        key = ("wages", id(trades), tile)
        kept = reads.get(key)
        if kept is None or kept[0] is not trades:
            found = {}
            for trade in trades:
                area = self.area_of(trade, tile)
                wage = reads.get(("wage", trade, area))
                if wage is None:
                    wage = reads[("wage", trade, area)] = wage_in_view(self.setup, self, trade, area)
                found[trade] = wage
            kept = reads[key] = (trades, found)
        return dict(kept[1])

    def interest_rate(self, currency: CurrencyId) -> Optional[float]:
        """Last year's base lending rate; None for a currency the memory holds no rate for (a plan that needs
        a rate is then not made; the economy's own currency always has one: `rates.own_rate`)."""
        return self._memory.rates.get(currency)

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

    def opening_wage_level(self, currency: CurrencyId) -> float:
        return self._memory.opening_wage_level(currency)

    def observed_inflation(self, currency: CurrencyId) -> Optional[float]:
        return self._memory.observed_inflation.get(currency)

    def equity(self, agent: AgentId) -> float:
        """What the agent owns of the firms: nothing counted in a view that has no firms (`CreditView` has them)."""
        return 0.0

    def claims(self, agent: AgentId, currency: CurrencyId) -> float:
        """What the agent expects to collect on loans it has made: nothing counted in a view that has no loans."""
        return 0.0

    def loss_rate(self, agent: AgentId, currency: CurrencyId) -> float:
        """The loss the agent expects per year of credit exposure: none in a view that has no loans."""
        return 0.0

    def cash(self, agent: AgentId, currency: CurrencyId) -> float:
        return self._book.balance(agent, currency)

    def stock(self, agent: AgentId, good: GoodId, tile: TileId) -> float:
        return self._book.stock(agent, good, tile)
