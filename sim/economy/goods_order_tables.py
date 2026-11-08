"""The year's goods orders and their clearing as tables (docs/architecture/COMPILED_YEAR.md, stage 2).

Six tables, all numbered with the book's and the market memory's ids (nothing here has a numbering of its own):

    GoodsBids          one row per bid, in the order the bids reached the book of orders; results are written in place
    GoodsOffers        one row per offer, likewise
    GoodsMarketResults one row per market cleared in the batched path, in the order the markets cleared
    GoodsPairs         one row per (bid, offer) pair that traded, markets one after another
    BidOrder, OfferOrder  the rows of each cleared market's bids and offers in clearing order, markets one after another

An agent id is `book.agent_number`, a good id `book.good_number`, a tile id `book.tile_number`; a market id is the row of the
market `good|area` in the market memory's goods table (`MarketTables.goods_markets`). A row is never reordered: the stable
order of a market's bids is the order of the rows, and "who sorts first" is a rank over names that the clearing computes
(`goods_name_ranks`), because ids are numbered by arrival and the rules sort by name.

Rows `0 .. row_count - 1` are in use (sim/compiled_tables/spec.py)."""
import numpy

from sim.compiled_tables.spec import Column, TableSpec

# What wrote an order. Informational: no rule reads it, so a mod's or a test's order is simply `OTHER`.
SOURCE_NAMES = ("other", "household", "tool", "store", "state", "mint", "producer_input", "producer_output", "merchant",
                "carrier", "land", "loan", "engine", "respend")
OTHER, HOUSEHOLD, TOOL, STORE, STATE, MINT, PRODUCER_INPUT, PRODUCER_OUTPUT, MERCHANT, CARRIER, LAND, LOAN, ENGINE, RESPEND = range(
    len(SOURCE_NAMES))

GOODS_BIDS = TableSpec("GoodsBids", (
    Column("buyer", numpy.int64, "the agent that wants the goods", "agent id", ids="agents"),
    Column("good", numpy.int64, "the good wanted", "good id", ids="goods"),
    Column("tile", numpy.int64, "where the goods are delivered", "tile id", ids="tiles"),
    Column("market", numpy.int64, "the goods market (good, area) the bid is made in", "goods market id", ids="goods markets"),
    Column("sequence", numpy.int64, "the number the bid arrived with; equal ties in the clearing order keep this order", "arrival number"),
    Column("priority", numpy.int64, "the need tier: lower clears first when a seller runs short at one price", "tier"),
    Column("floor_quantity", numpy.float64, "what the buyer needs whatever the price", "good units"),
    Column("flexible_quantity", numpy.float64, "what the buyer adds at the reference price, falling as the price rises", "good units"),
    Column("reference_price", numpy.float64, "the price at which the flexible quantity is wanted", "currency units per unit"),
    Column("elasticity", numpy.float64, "how fast the flexible quantity falls as the price rises", "dimensionless"),
    Column("budget", numpy.float64, "the most money the bid can spend; the budget caps the quantity", "currency units"),
    Column("maximum_price", numpy.float64, "above this price the buyer takes nothing (infinity: no ceiling)", "currency units per unit"),
    Column("source", numpy.int64, "what wrote the bid (a SOURCE_NAMES code); informational", "source code"),
    Column("position", numpy.int64, "result: the bid's place in its market's bids in clearing order (priority, buyer name, tile name); -1 until cleared", "place"),
    Column("quantity_bought", numpy.float64, "result: the units the bid took in the first clearing", "good units"),
    Column("cost", numpy.float64, "result: the money the units cost, at each seller's ask", "currency units"),
))
GoodsBids = GOODS_BIDS.make_type(__name__)

GOODS_OFFERS = TableSpec("GoodsOffers", (
    Column("seller", numpy.int64, "the agent that sells", "agent id", ids="agents"),
    Column("good", numpy.int64, "the good offered", "good id", ids="goods"),
    Column("tile", numpy.int64, "where the goods are", "tile id", ids="tiles"),
    Column("market", numpy.int64, "the goods market (good, area) the offer is made in", "goods market id", ids="goods markets"),
    Column("sequence", numpy.int64, "the number the offer arrived with; equal ties keep this order", "arrival number"),
    Column("quantity", numpy.float64, "the units for sale", "good units"),
    Column("reservation_price", numpy.float64, "the lowest price the seller takes; the clearing's repricing overwrites it with the ask chosen", "currency units per unit"),
    Column("stock_slot", numpy.int64, "the seller's book stock slot for (seller, good, tile), -1 where it holds none", "stock slot"),
    Column("source", numpy.int64, "what wrote the offer (a SOURCE_NAMES code); informational", "source code"),
    Column("rank", numpy.int64, "result: the offer's place in its market's offers by ask, cheapest first; -1 until cleared", "place"),
    Column("ask", numpy.float64, "result: the price the offer sold at (its reservation, raised to the market's token minimum)", "currency units per unit"),
    Column("quantity_sold", numpy.float64, "result: the units sold in the first clearing", "good units"),
    Column("quantity_left", numpy.float64, "result: the units not sold, after each (seller, tile)'s sales are taken off its offers in turn", "good units"),
))
GoodsOffers = GOODS_OFFERS.make_type(__name__)

GOODS_MARKET_RESULTS = TableSpec("GoodsMarketResults", (
    Column("market", numpy.int64, "the goods market cleared", "goods market id", ids="goods markets"),
    Column("traded", numpy.uint8, "flag: the market traded (otherwise it has a quote and no price)", "0 or 1"),
    Column("quantity", numpy.float64, "the units traded", "good units"),
    Column("price", numpy.float64, "the mean ask the units sold at, weighted by quantity", "currency units per unit"),
    Column("demand_at_price", numpy.float64, "what the buyers asked for at the asks they faced, before any seller ran out", "good units"),
    Column("offered_at_price", numpy.float64, "the units on offer", "good units"),
    Column("first_bid_slot", numpy.int64, "first slot of the market's bids in the bid order table", "slot"),
    Column("bid_count", numpy.int64, "how many bids the market has", "count"),
    Column("first_offer_slot", numpy.int64, "first slot of the market's offers with units in the offer order table", "slot"),
    Column("offer_count", numpy.int64, "how many offers with units the market has", "count"),
    Column("first_pair", numpy.int64, "first row of the market's pairs", "row"),
    Column("pair_count", numpy.int64, "how many pairs the market has", "count"),
))
GoodsMarketResults = GOODS_MARKET_RESULTS.make_type(__name__)

GOODS_PAIRS = TableSpec("GoodsPairs", (
    Column("bid_row", numpy.int64, "the row of the bid that bought", "bid row"),
    Column("offer_row", numpy.int64, "the row of the offer that sold", "offer row"),
    Column("quantity", numpy.float64, "the units the bid bought from the offer, at the offer's ask", "good units"),
))
GoodsPairs = GOODS_PAIRS.make_type(__name__)

BID_ORDER = TableSpec("BidOrder", (
    Column("bid_row", numpy.int64, "a bid's row; each cleared market's bids one after another, in clearing order", "bid row"),
))
BidOrder = BID_ORDER.make_type(__name__)

OFFER_ORDER = TableSpec("OfferOrder", (
    Column("offer_row", numpy.int64, "an offer's row; each cleared market's offers with units one after another, in seller-and-tile order", "offer row"),
))
OfferOrder = OFFER_ORDER.make_type(__name__)
