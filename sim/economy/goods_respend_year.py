"""The year's second round of household buying: after every market has cleared, a cohort rationed in some market bids
what it could not spend on the goods still offered (goods_respend.py), the markets clear again against the stock left,
and a cohort still rationed goes on until nothing more is bought. Money no offered good takes stays with the cohort.
All the rounds run in one kernel over every rationed cohort and market (goods_respend_kernel.py).
"""
import math
from typing import Dict, Tuple

import numpy


from sim.constants import declare

from . import bid_order, goods_respend_pack, goods_respend_unpack
from .bid_columns import BidColumns, MarketBids, columns_of_bids, joined, order_of_bids
from .goods_table_views import LazyObjects
from .goods_market import MINIMUM_PRICE_SHARE_OF_REFERENCE
from .goods_respend import RESPEND_NEGLIGIBLE_ROUND_SHARE
from .goods_respend_kernel import respend_rounds
from .goods_added_bids import AddedBids
from .goods_year_markets import YearMarkets
from sim.book import ROUNDING_SHARE

Market = Tuple[str, str]

RESPEND_APPORTIONED_WANTED_SHARE = declare(
    "RESPEND_APPORTIONED_WANTED_SHARE", 1.0, kind="temporary_heuristic",
    unit="share of the round's wanted counted for the bids that add demand",
    source=None, confidence="D",
    why="A respend round's clearing gives the demand of all its bids together; the part that is new demand is taken "
        "pro rata to the adding bids' demand at one price, not computed bid by bid at the asks each faced.",
    retire="Complaint 964 exact wanted quantity per bid")


def _cell(column: str, meaning: str) -> property:
    """A float property reading and writing the market's cell of `column` in the year's table."""
    def read(self) -> float:
        return float(getattr(self.year_markets.table, column)[self.row])

    def write(self, figure: float) -> None:
        getattr(self.year_markets.table, column)[self.row] = figure

    return property(read, write, doc=meaning)


class LeftMarket:
    """A cleared market as the second round finds it: its bids and first-round result, the offers with what sold taken
    off, its last price, what has been delivered in it, what its buyers wanted (`wanted_in_round`, summed over the
    rounds), the bids that add demand in each round (`bids_adding_demand`) and the clearings of every round. What is unsold is what the last round to
    clear it left on offer. A market on the order tables carries its `rows` (goods_market_rows.MarketRows); its `bids` and
    `offers` are then built only when something reads them."""

    def __init__(self, bids, result, offers, last_price, delivered, wanted, idle_years=0, bought=None, rows=None, year_markets=None, row=None):
        year_markets_shared = year_markets is not None
        if year_markets is None:       # a market made alone has a table of its own
            year_markets = YearMarkets(1)
            row = year_markets.claim(1)
            year_markets.fill(row, [delivered], [wanted], [result.offered_at_price], [delivered], [idle_years],
                              [math.nan if last_price is None else last_price])
        self.year_markets = year_markets    # the figures below are the cells of `row` of this table (`goods_year_markets.py`); where the
        self.row = row                      # year's markets share one table, the caller fills the cells of all of them at once
        self.results = [result]
        self._later = None if year_markets_shared else []    # the respend rounds' clearings as (quantity, price or None, demand at price, offered at price)
        self.bought = bought or {}     # buyer -> (units received, money paid) in the first round's settlement
        self._bids = bids
        self._added = None             # the later rounds' bids that add demand, as columns (`goods_added_bids.AddedBids`)
        self._added_read = not year_markets_shared
        self._all_bids = list(bids) if bids is not None and rows is None else None     # a market on the objects: the first round's bids and the added ones
        self.rows = rows
        self.result = result
        self._offers = offers

    @property
    def later(self) -> list:
        """The respend rounds' clearings as (quantity, price or None, demand at price, offered at price), in the order they were run (read from
        the year's table the first time, for a market that shares it)."""
        if self._later is None:
            self._later = self.year_markets.later_of(self.row)
        return self._later

    @property
    def added(self):
        """The bids later rounds added to the market (`goods_added_bids.AddedBids`), or None; made from the year's table when first read."""
        if not self._added_read:
            self._added_read = True
            found = self.year_markets.added_of(self.row)
            if found is not None:
                buyers, tiles, *figures = found
                good, area = self._good_area()
                self._added = AddedBids(good, area, buyers, tiles, *figures)
        return self._added

    @added.setter
    def added(self, added) -> None:
        self._added, self._added_read = added, True

    def _good_area(self):
        return self.result.good, self.result.area

    delivered = _cell("delivered", "goods moved in all rounds so far")
    wanted = _cell("wanted", "what buyers asked for in all rounds so far")
    last_offered = _cell("last_offered", "on offer at the last round's price")
    last_delivered = _cell("last_delivered", "moved in the last round")

    @property
    def idle_years(self) -> int:
        """Years the market lacked bids or offers, before this year."""
        return int(self.year_markets.table.idle_years[self.row])

    @idle_years.setter
    def idle_years(self, years: int) -> None:
        self.year_markets.table.idle_years[self.row] = years

    @property
    def last_price(self):
        """The price the market's memory held when the year began (None: none)."""
        price = float(self.year_markets.table.last_price[self.row])
        return None if price != price else price

    @last_price.setter
    def last_price(self, price) -> None:
        self.year_markets.table.last_price[self.row] = math.nan if price is None else price

    @property
    def bids(self):
        """The first round's bids (built from the rows when read, for a market on the tables)."""
        if self._bids is None:
            self._bids = self.rows.bids_lazy()
        return self._bids

    @bids.setter
    def bids(self, bids) -> None:
        self._bids = bids

    @property
    def offers(self):
        """The offers with what sold taken off (built from the rows when read, for a market on the tables)."""
        if self._offers is None:
            if self.year_markets.first_round_filled:       # the units each offer has left are in the year's table (the respend changes them there)
                first = int(self.year_markets.table.left_first[self.row])
                units = self.year_markets.left_units()[first:first + len(self.rows.left_array)].tolist()
                self._offers = LazyObjects(lambda: self.rows.offer_objects(units), sum(1 for each in units if each > 0.0))
            else:
                self._offers = self.rows.left_lazy()
        return self._offers

    @offers.setter
    def offers(self, offers) -> None:
        self._offers = offers
        self.year_markets.table.left_count[self.row] = len(offers)

    @property
    def all_bids(self):
        """The first round's bids and the later rounds' that add demand."""
        if self._all_bids is not None:
            return self._all_bids
        if self.added is None:
            return self.bids
        return LazyObjects(lambda: list(self.bids) + self.added.bids(), len(self.rows.bid_rows) + len(self.added))

    @all_bids.setter
    def all_bids(self, bids) -> None:
        self._all_bids = bids

    def market_bids(self, place=None, block=None) -> MarketBids:
        """The first round's bids and those later rounds added, for the entry rules: columns (read from the order tables' rows, with the added
        bids' columns after them), and the objects of `all_bids` when a rule asks for them. With the market's `place` in the year's bids block
        (`year_bids.YearBids`) the columns are views of the block's rows."""
        count = len(self.all_bids) if block is None else block.count(place)
        make_columns = self._bid_columns if block is None else (lambda: block.columns_at(place))
        return MarketBids(make_columns, lambda: list(self.all_bids), count, self._bid_order)

    def _bid_order(self):
        if self.rows is None:
            return order_of_bids(list(self.all_bids))
        return bid_order.clearing_order(self.rows, self.added)

    def _bid_columns(self) -> BidColumns:
        if self.rows is None:
            return columns_of_bids(list(self.all_bids))
        table = self.rows.orders.tables()[0]
        rows = self.rows.bid_array
        first = BidColumns(table.floor_quantity[rows], table.flexible_quantity[rows], table.reference_price[rows], table.elasticity[rows],
                           table.budget[rows], table.maximum_price[rows])
        return first if self.added is None else joined(first, self.added.columns())

    def add_bids(self, added) -> None:
        """The bids a later round added to this market (`goods_added_bids.AddedBids`): kept as columns, and as objects too for a market on the
        objects."""
        self.added = added
        if self._all_bids is not None:
            self._all_bids.extend(added.bids())

    def leave_units(self, units) -> None:
        """The units each offer left in `rows` has after the rounds (zero: sold out); the offers are built from them when read."""
        kept = sum(1 for each in units if each > 0.0)
        self._offers = LazyObjects(lambda: self.rows.offer_objects(units), kept)
        self.year_markets.table.left_count[self.row] = kept

    @property
    def unsold(self) -> float:
        """What the last round to clear this market left on offer."""
        return max(0.0, self.last_offered - self.last_delivered)


def respend(setup, record, view, ledger, markets: Dict[Market, LeftMarket], basket_of, orders=None) -> None:
    """Clear the households' leftover bids against the stock left in `markets`, in rounds, and settle them."""
    packed = goods_respend_pack.pack(setup, record, view, ledger, markets, basket_of, orders)
    if packed is None:
        return
    out = run_rounds(packed)
    goods_respend_unpack.write_markets(setup, ledger, markets, packed, out)
    goods_respend_unpack.write_settlement(setup, record, ledger, packed, out)


CHANGED_BY_KERNEL = ("has_bid", "offer_quantity", "key_stock", "agent_cash")


def run_rounds(packed):
    """The kernel's answer for `packed`, run again with room for more rows while its logs are full. The arrays the kernel
    changes are copied for each run; those of the last run replace them in `packed.arguments`."""
    capacity = max(4096, 8 * len(packed.arguments["first_market"]))
    while True:
        arguments = {name: array.copy() if name in CHANGED_BY_KERNEL else array
                     for name, array in packed.arguments.items()}
        out = respend_rounds(*arguments.values(), RESPEND_APPORTIONED_WANTED_SHARE, RESPEND_NEGLIGIBLE_ROUND_SHARE,
                             MINIMUM_PRICE_SHARE_OF_REFERENCE, ROUNDING_SHARE, capacity)
        if not out[0]:
            packed.arguments = arguments
            return out
        capacity *= 4
