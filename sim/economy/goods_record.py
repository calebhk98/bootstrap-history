"""What the economy keeps about its goods markets from year to year: last year's volumes and books, the opening's basket, and output."""
from dataclasses import dataclass, field
from typing import Any, Dict

from .goods_market_column import MarketColumn
from .record_parts import OwnedRecord
from .types import TileId


def _unmarked() -> MarketColumn:
    return MarketColumn()


def _streaks() -> MarketColumn:
    return MarketColumn(integer=True)


def _saved(column) -> Dict[str, Any]:
    return column.saved() if isinstance(column, MarketColumn) else dict(column)


def _loaded(data: Dict[str, Any]) -> MarketColumn:
    column = MarketColumn()
    column.hold_named(list(data), list(data.values()))
    return column


def _loaded_streaks(data: Dict[str, Any]) -> MarketColumn:
    column = MarketColumn(integer=True)
    column.hold_named(list(data), list(data.values()))
    return column


@dataclass
class GoodsRecord(OwnedRecord):
    volumes: MarketColumn = field(default_factory=_unmarked)             # market_key -> units delivered last year in all rounds; a market with no orders is absent (a column of the memory's goods-market numbering)
    unsold: MarketColumn = field(default_factory=_unmarked)              # market_key -> units offered beyond what was delivered last year (a column)
    unmet: MarketColumn = field(default_factory=_unmarked)               # market_key -> units buyers asked for at the asks they faced beyond what was delivered last year (a column)
    curves: Dict[str, Any] = field(default_factory=dict)                 # market_key -> the first round's book at the port, before any sale or respend (market_curves.py)
    margin_years: MarketColumn = field(default_factory=_streaks)         # market_key -> years in a row the expected price stood above the entry price (a column of whole numbers)
    index_base_prices: Dict[str, float] = field(default_factory=dict)    # the price level's base; opening if empty
    opening_basket: Dict[str, float] = field(default_factory=dict)       # good -> quantity at the opening, as far as the opening supplies it
    opening_demand: Dict[str, float] = field(default_factory=dict)       # good -> quantity households were seeded to want, supplied or not
    opening_demand_by_country: Dict[str, Dict[str, float]] = field(default_factory=dict)  # country -> good -> quantity its households were seeded to want
    buyer_limits: Dict[str, float] = field(default_factory=dict)         # good -> the highest price a household bid for it took units at when it last cleared (ask_ceiling.buyer_limit)
    output_by_tile: Dict[TileId, Dict[str, float]] = field(default_factory=dict)   # tile -> good -> units the home producers made last year

    OWNERS = ("goods_record", "year_goods", "entry_margin", "goods_good_clear")
    ENCODERS = {"volumes": _saved, "unsold": _saved, "unmet": _saved, "margin_years": _saved}
    DECODERS = {"volumes": _loaded, "unsold": _loaded, "unmet": _loaded, "margin_years": _loaded_streaks}
    COLUMNS = ("volumes", "unsold", "unmet", "margin_years")      # the stores held as columns of the memory's goods-market numbering (`bind_markets`)
    MARKET_KEYED = ("volumes", "unsold", "unmet", "margin_years", "curves")    # the stores keyed by market_key(good, area): they move when the areas are redrawn

    def bind_markets(self, tables) -> None:
        """Index the columns by the record's market numbering, keeping their figures."""
        for name in self.COLUMNS:
            column = getattr(self, name)
            if isinstance(column, MarketColumn):
                column.bind(tables)

    def note_buyer_limit(self, good: str, limit) -> None:
        """The household bids for `good` took units up to `limit` this year (None: no bid took any)."""
        if limit is None:
            self.buyer_limits.pop(good, None)
        else:
            self.buyer_limits[good] = limit

    def reset_output(self) -> None:
        self.output_by_tile = {}

    def add_output(self, tile: TileId, good: str, quantity: float) -> None:
        """The home producers on `tile` made `quantity` more of `good`."""
        row = self.output_by_tile.setdefault(tile, {})
        row[good] = row.get(good, 0.0) + quantity

    def set_index_base_prices(self, prices: Dict[str, float]) -> None:
        """The price level's base."""
        self.index_base_prices = prices

    def seed_opening_demand(self, demand: Dict[str, float], demand_by_country: Dict[str, Dict[str, float]]) -> None:
        self.opening_demand = demand
        self.opening_demand_by_country = demand_by_country

    def seed_opening_basket(self, basket: Dict[str, float]) -> None:
        self.opening_basket = basket
