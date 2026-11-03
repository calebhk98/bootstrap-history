"""What the economy keeps about its goods markets from year to year: last year's volumes and books, the opening's basket, and output."""
from dataclasses import dataclass, field
from typing import Any, Dict

from .record_parts import OwnedRecord
from .types import TileId


@dataclass
class GoodsRecord(OwnedRecord):
    volumes: Dict[str, float] = field(default_factory=dict)              # market_key -> units delivered last year in all rounds; a market with no orders is absent
    unsold: Dict[str, float] = field(default_factory=dict)               # market_key -> units offered beyond what was delivered last year
    unmet: Dict[str, float] = field(default_factory=dict)                # market_key -> units buyers asked for at the asks they faced beyond what was delivered last year
    curves: Dict[str, Any] = field(default_factory=dict)                 # market_key -> the first round's book at the port, before any sale or respend (market_curves.py)
    margin_years: Dict[str, int] = field(default_factory=dict)           # market_key -> years in a row the expected price stood above the entry price
    index_base_prices: Dict[str, float] = field(default_factory=dict)    # the price level's base; opening if empty
    opening_basket: Dict[str, float] = field(default_factory=dict)       # good -> quantity at the opening, as far as the opening supplies it
    opening_demand: Dict[str, float] = field(default_factory=dict)       # good -> quantity households were seeded to want, supplied or not
    opening_own_grown: Dict[str, float] = field(default_factory=dict)    # good -> quantity households were seeded to grow on their own plots
    opening_demand_by_country: Dict[str, Dict[str, float]] = field(default_factory=dict)  # country -> good -> quantity its households were seeded to want
    output_by_tile: Dict[TileId, Dict[str, float]] = field(default_factory=dict)   # tile -> good -> units the home producers made last year

    OWNERS = ("goods_record", "year_goods", "entry_margin")

    def reset_output(self) -> None:
        self.output_by_tile = {}

    def add_output(self, tile: TileId, good: str, quantity: float) -> None:
        """The home producers on `tile` made `quantity` more of `good`."""
        row = self.output_by_tile.setdefault(tile, {})
        row[good] = row.get(good, 0.0) + quantity

    def set_index_base_prices(self, prices: Dict[str, float]) -> None:
        """The price level's base."""
        self.index_base_prices = prices

    def seed_opening_own_grown(self, own_grown: Dict[str, float]) -> None:
        self.opening_own_grown = own_grown

    def seed_opening_demand(self, demand: Dict[str, float], demand_by_country: Dict[str, Dict[str, float]]) -> None:
        self.opening_demand = demand
        self.opening_demand_by_country = demand_by_country

    def seed_opening_basket(self, basket: Dict[str, float]) -> None:
        self.opening_basket = basket
