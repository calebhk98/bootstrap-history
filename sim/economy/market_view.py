"""The read-only view agents plan from, over the market memory's arrays, the book and the area map."""
from typing import Dict, Optional

from sim.book import Book
from .market_arrays import KEY_SEPARATOR
from .market_memory import MarketMemory, _writes
from .types import AgentId, AreaId, CurrencyId, GoodId, TileId, TradeId


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
        self._keys_of_names: Dict[int, tuple] = {}     # id of a names tuple -> (names, tile -> market keys)
        self._area_by_tile: Dict[str, Dict[TileId, AreaId]] = {}    # name -> tile -> its area; the area map does not change
        self._stamp = _writes[0]
        self._reads: Dict[tuple, object] = {}     # reads of the memory kept until the next write to it

    def prices_across(self, good: GoodId, areas) -> list:
        """`price(good, area.area_id)` for each of `areas` (the good's areas), in order."""
        keys = self._keys_of_good.get(good)
        if keys is None or keys[0] is not areas:
            keys = self._keys_of_good[good] = (areas, [good + KEY_SEPARATOR + area.area_id for area in areas])
        prices = self._memory.prices
        return list(map(prices.get, keys[1]))

    def price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """The planning price: the remembered price, last year's trade blended with the older price in proportion to
        the trade's share of the market's usual volume (`year_goods.remembered_price`), or, where nothing traded,
        the quote (`price_kind` says which); None where the market has no price. A reader that needs the price
        both sides agreed to last year uses `cleared_price`."""
        return self._memory.prices.get_pair(good, area)

    def offered_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """What a buyer can buy at: the traded price or an ask still posted (`MarketMemory.offered_price`); None
        where nothing is on offer. A buyer reads this, never `price`."""
        cell = self._memory.cell_of(good, area)
        return None if cell is None else self._memory.offered_price_at(cell)

    def present_prices_at(self, names: tuple, tile: TileId) -> Dict[str, float]:
        """`price` of each of `names` (goods, one tuple kept by the caller) in its area on `tile`, those with a
        price only, in order: the keys are built once per names tuple and tile."""
        kept = self._keys_of_names.get(id(names))
        if kept is None or kept[0] is not names:
            kept = self._keys_of_names[id(names)] = (names, {})
        keys = kept[1].get(tile)
        if keys is None:
            keys = kept[1][tile] = tuple(name + KEY_SEPARATOR + self.area_of(name, tile) for name in names)
        reads = self._current()
        read_key = ("present", id(names), tile)
        kept_found = reads.get(read_key)
        if kept_found is None or kept_found[0] is not names:
            found = {}
            for name, key in zip(names, keys):
                figure = self._memory.prices.get(key)
                if figure is not None:
                    found[name] = figure
            kept_found = reads[read_key] = (names, found)
        return dict(kept_found[1])

    def price_kind(self, good: GoodId, area: AreaId) -> Optional[str]:
        """PRICE_SMOOTHED_TRADE, or the kind of quote or estimate `price` is; None when the market has no price."""
        cell = self._memory.cell_of(good, area)
        return None if cell is None else self._memory.price_kind_at(cell)

    def cleared_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """The price the market cleared at last year; None when nothing traded in it."""
        return self._memory.cleared_prices.get_pair(good, area)

    def usual_price(self, good: GoodId, area: AreaId) -> Optional[float]:
        """A slow average of the price, what holders compare today's price with; None before any."""
        return self._memory.usual_prices.get_pair(good, area)

    def wage(self, trade: TradeId, area: AreaId) -> Optional[float]:
        return self._memory.wages.get_pair(trade, area)

    def wages_block(self, trades, areas):
        """The recorded wage of each of `trades` in each of `areas` as one (trades by areas) array, NaN where the memory holds none."""
        ids = self._memory.numbering("trades")
        return self._memory.wages.gather(ids.rows_of(trades), ids.columns_of(areas))

    def wage_held_anywhere(self, trade: TradeId) -> bool:
        """Whether the memory holds a wage for the trade in any area (`MarketMemory.holds_wage_for`)."""
        return self._memory.holds_wage_for(trade)

    def _current(self) -> Dict[tuple, object]:
        """The cached reads, dropped when the memory has been written to since they were made."""
        if self._stamp != _writes[0]:
            self._stamp = _writes[0]
            self._reads = {}
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
