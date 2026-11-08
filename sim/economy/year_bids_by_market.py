"""`YearLedger.bids_by_market` over the year's bids block: each market's `bid_columns.MarketBids` is made when first asked for (a market no
reader asks about costs nothing), with columns that are views of the block's rows (`year_bids.YearBids`)."""
from collections.abc import Mapping
from typing import Dict, Iterator, Tuple

from .bid_columns import MarketBids
from .year_bids import YearBids

Market = Tuple[str, str]


class BidsByMarket(Mapping):
    """Market -> `MarketBids` for the markets of a block, built on first read from the cleared markets (`goods_respend_year.LeftMarket`)."""

    def __init__(self, block: YearBids, left_markets: Dict[Market, object]):
        self._block, self._left = block, left_markets
        self._made: Dict[Market, MarketBids] = {}

    def __getitem__(self, market: Market) -> MarketBids:
        found = self._made.get(market)
        if found is None:
            place = self._block.index[market]      # a market that is not in the block raises KeyError, as a dictionary does
            found = self._made[market] = self._left[market].market_bids(place, self._block)
        return found

    def __iter__(self) -> Iterator[Market]:
        return iter(self._block.markets)

    def __len__(self) -> int:
        return len(self._block.markets)

    def __contains__(self, market) -> bool:
        return market in self._block.index
