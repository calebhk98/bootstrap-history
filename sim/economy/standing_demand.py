"""Demand that is settled outside the book but is still demand: a project's draw on a material, which the engine
pays at the market edge. Firm entry reads the year's bids (entry_year.py); these join them there, so a good only
such a buyer asks for draws a maker as a household's or a merchant's bid does. Nothing here clears."""
from typing import Dict, List, Mapping, Sequence, Tuple

from .bid_columns import MarketBids, columns_of, columns_of_bids, joined
from .types import AreaId, Bid, GoodId


def _plain(base: Sequence[Bid]) -> MarketBids:
    """A market's bids with no standing bid joined, as `MarketBids`."""
    return MarketBids(lambda: columns_of(base), lambda: list(base), len(base))


class _WithStanding(Mapping):
    """The year's bids by market with the standing bids joined to their markets; a market with none is the list (lazy where it sits
    on the order tables) the year holds, left unread until someone reads it."""

    def __init__(self, bids_by_market: Mapping, standing: Dict[Tuple[GoodId, AreaId], List[Bid]]):
        self._base, self._standing = bids_by_market, standing
        self._joined: dict = {}

    def __getitem__(self, key):
        base = self._base.get(key, ())
        standing = self._standing.get(key)
        if not standing:
            return base if isinstance(base, MarketBids) else _plain(base)
        found = self._joined.get(key)
        if found is None:      # one object per market, so its columns are joined once however often the rules read it
            found = self._joined[key] = MarketBids(lambda: joined(columns_of(base), columns_of_bids(standing)), lambda: list(base) + standing,
                                                   len(base) + len(standing))
        return found

    def __iter__(self):
        return iter(sorted(set(self._base) | set(self._standing)))

    def __len__(self) -> int:
        return len(set(self._base) | set(self._standing))


def with_standing_bids(bids_by_market: Mapping[Tuple[GoodId, AreaId], Sequence[Bid]],
                       standing_bids: Sequence[Bid]) -> Mapping[Tuple[GoodId, AreaId], Sequence[Bid]]:
    """The year's bids by market with the standing bids added to their markets."""
    standing: Dict[Tuple[GoodId, AreaId], List[Bid]] = {}
    for bid in standing_bids:
        standing.setdefault((bid.good, bid.area), []).append(bid)
    return _WithStanding(bids_by_market, standing)
