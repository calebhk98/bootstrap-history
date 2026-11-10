"""The market memory's tables: one row per market, one column per remembered figure.

Two tables, each indexed by the market's number in its `IdTable` (`MarketTables` holds the numberings):

- goods markets, named `good|area` (`GOODS_MARKETS`): the eight stores that used to be dicts keyed by `market_key(good, area)`;
- labour markets, named `trade|labour area` (`LABOUR_MARKETS`): the remembered wages.

A figure a market does not hold is NaN (float columns) or an unset bit in `held` (whole-number and kind columns); never 0.
A store (`prices`, `trade_age`, ...) is the set of markets that hold its figure. The mappings the memory has always shown
(`MarketMemory.prices` and the rest) list a store in the order its markets were added to it, as a dict did, which is what
`order_*` records: each store has its own counter (`MarketTables.next_order`) and a market takes the next number when it
enters the store. A kernel that adds a market to a store must take that number and count the member
(`MarketTables.member_count`), or the mapping and the table disagree."""
import numpy

from sim.compiled_tables.spec import Column, TableSpec

KEY_SEPARATOR = "|"          # a market's name is first + KEY_SEPARATOR + area (`market_memory.market_key`)

PRICES, USUAL_PRICES, CLEARED_PRICES, VOLUME_WEIGHTS, TRADE_AGE, YEARS_WITHOUT_BIDS, YEARS_WITHOUT_OFFERS, QUOTE_KINDS, WAGES = range(9)
STORE_COUNT = 9
GOODS_STORE_COUNT = 8       # stores 0..7 are columns of the goods table; WAGES is a column of the labour table

HELD_TRADE_AGE, HELD_YEARS_WITHOUT_BIDS, HELD_YEARS_WITHOUT_OFFERS, HELD_QUOTE_KIND = 1, 2, 4, 8     # bits of `held`

_MARKET_FACTS = (
    Column("first", numpy.int64, "the good (goods market) or trade (labour market) the market is for", "good or trade id", ids="goods or trades"),
    Column("area", numpy.int64, "the market area (goods) or labour area (labour) of the market", "area id", ids="areas"),
)

GOODS_MARKETS = TableSpec("GoodsMarkets", _MARKET_FACTS + (
    Column("held", numpy.int64, "which of trade_age, years_without_bids, years_without_offers and quote_kind hold a figure (HELD_* bits)", "bit set"),
    Column("price", numpy.float64, "the remembered price, last year's trade blended with the older price or a quote; NaN: none", "currency units per unit"),
    Column("usual_price", numpy.float64, "a slow average of the price; NaN: none yet", "currency units per unit"),
    Column("cleared_price", numpy.float64, "the price the market cleared at last year; NaN: it did not trade", "currency units per unit"),
    Column("volume_weight", numpy.float64, "the market's usual volume, smoothed; NaN: none yet", "units per year"),
    Column("trade_age", numpy.int64, "years since the market last cleared, 0 for last year (only where HELD_TRADE_AGE)", "years"),
    Column("years_without_bids", numpy.int64, "years in a row the market had offers and nobody bidding (only where HELD_YEARS_WITHOUT_BIDS)", "years"),
    Column("years_without_offers", numpy.int64, "years in a row the market had bids and no seller (only where HELD_YEARS_WITHOUT_OFFERS)", "years"),
    Column("quote_kind", numpy.int64, "what `price` holds when nothing traded, a number in the quote kinds IdTable (only where HELD_QUOTE_KIND)", "quote kind id", ids="kinds"),
    Column("order_price", numpy.int64, "place of the market in the order markets entered the price store", "entry number"),
    Column("order_usual_price", numpy.int64, "place in the usual price store", "entry number"),
    Column("order_cleared_price", numpy.int64, "place in the cleared price store", "entry number"),
    Column("order_volume_weight", numpy.int64, "place in the volume weight store", "entry number"),
    Column("order_trade_age", numpy.int64, "place in the trade age store", "entry number"),
    Column("order_years_without_bids", numpy.int64, "place in the years-without-bids store", "entry number"),
    Column("order_years_without_offers", numpy.int64, "place in the years-without-offers store", "entry number"),
    Column("order_quote_kind", numpy.int64, "place in the quote kind store", "entry number"),
))
GoodsMarkets = GOODS_MARKETS.make_type(__name__)

LABOUR_MARKETS = TableSpec("LabourMarkets", _MARKET_FACTS + (
    Column("wage", numpy.float64, "the remembered wage; NaN: none", "currency units per hour"),
    Column("order_wage", numpy.int64, "place of the market in the order markets entered the wage store", "entry number"),
))
LabourMarkets = LABOUR_MARKETS.make_type(__name__)
