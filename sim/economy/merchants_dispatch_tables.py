"""The columns one year's dispatch of every merchant works over (`merchants_dispatch_kernel`), one table per kind of row.

A pair is a (source tile, destination tile) haul: what a tonne costs, needs and wears on it. A route is what one merchant holds
at a (good, source tile) and the legs it is shared over; a leg is one destination of it. A merchant row carries its purse, its
crew hours hired by crew key and its fleet by carrier good. Crew keys (`market_key(trade, tile)`) and carrier goods are numbered
for the year by the caller. A column with a width has that many places a row; a place past the row's count is padding."""
import numpy

from sim.compiled_tables.spec import Column, TableSpec

PAIRS = TableSpec("DispatchPairs", [
    Column("cost", numpy.float64, "what a tonne costs to carry (the fee)", "money per tonne"),
    Column("money", numpy.float64, "what the carriers a tonne wears and the animals eat cost; NaN: no carrier price", "money per tonne"),
    Column("crew_count", numpy.int64, "crew keys a tonne needs hours of", "rows"),
    Column("crew_key", numpy.int64, "the crew key's number, in key order", "crew key", width=1),
    Column("crew_hours", numpy.float64, "crew hours a tonne needs of the key", "hours per tonne", width=1),
    Column("wear_count", numpy.int64, "carrier goods a tonne wears", "rows"),
    Column("wear_carrier", numpy.int64, "the carrier good's number", "carrier good", width=1),
    Column("wear_units", numpy.float64, "units of the carrier a tonne wears", "units per tonne", width=1),
    Column("dues_count", numpy.int64, "holders owed dues on the haul", "rows"),
    Column("dues_owed", numpy.float64, "dues a tonne owes the holder, holders in name order", "money per tonne", width=1),
])
DispatchPairs = PAIRS.make_type(__name__)

ROUTES = TableSpec("DispatchRoutes", [
    Column("merchant", numpy.int64, "the merchant's row in the merchants table", "merchant row"),
    Column("unit_mass_kg", numpy.float64, "the good's mass", "kg per unit"),
    Column("held", numpy.float64, "what the merchant holds on the source tile", "units"),
    Column("first_leg", numpy.int64, "its first leg", "leg row"),
    Column("leg_count", numpy.int64, "its legs", "legs"),
])
DispatchRoutes = ROUTES.make_type(__name__)

LEGS = TableSpec("DispatchLegs", [
    Column("pair", numpy.int64, "the haul's pair row; -1 where the destination is the source tile (nothing is carried)", "pair row"),
    Column("weight", numpy.float64, "the share of the route's stock the leg takes, by weight", "weight"),
    Column("spread", numpy.float64, "the merchant's expected price at the destination less at the source (what the haul gains)", "money per unit"),
])
DispatchLegs = LEGS.make_type(__name__)

MERCHANTS = TableSpec("DispatchMerchants", [
    Column("dispatching", numpy.int64, "1 when the merchant carries this year", "flag"),
    Column("cash", numpy.float64, "its purse; the kernel moves it as fees, dues and rents are paid", "money"),
    Column("has_plan", numpy.int64, "1 when crew hours were hired for it (its shipments are cut to them)", "flag"),
    Column("first_route", numpy.int64, "its first route, routes in (good, source tile) order", "route row"),
    Column("route_count", numpy.int64, "its routes", "routes"),
    Column("market_wage", numpy.float64, "what an hour of the crew key was last paid in its market", "money per hour", width=1),
    Column("hired_hours", numpy.float64, "crew hours hired, by crew key", "hours", width=1),
    Column("paid_wage", numpy.float64, "the average pay an hour hired was paid, by crew key; NaN: none hired", "money per hour", width=1),
    Column("fleet_capacity", numpy.float64, "wear a year its fleet and hired fleet bear, by carrier good", "units", width=1),
    Column("own_capacity", numpy.float64, "wear a year its own fleet bears, by carrier good", "units", width=1),
    Column("fleet_hired", numpy.float64, "wear a year it hired from others, by carrier good", "units", width=1),
    Column("fleet_hired_named", numpy.int64, "1 where the carrier good is among those it hired", "flag", width=1),
])
DispatchMerchants = MERCHANTS.make_type(__name__)

LEG_RESULTS = TableSpec("DispatchLegResults", [
    Column("carried", numpy.float64, "units carried on the leg", "units"),
    Column("fee", numpy.float64, "the fee paid the carrier, after the purse's cut", "money"),
    Column("dues_paid", numpy.float64, "the dues paid each holder of the pair, in the pair's order", "money", width=1),
])
DispatchLegResults = LEG_RESULTS.make_type(__name__)

MERCHANT_RESULTS = TableSpec("DispatchMerchantResults", [
    Column("hours_wanted", numpy.float64, "crew hours its shipments needed, by crew key, before any cut", "hours", width=1),
    Column("hours_wanted_named", numpy.int64, "1 where the crew key was asked for", "flag", width=1),
    Column("money_wanted", numpy.float64, "the carriage money those hours stand for, by crew key", "money", width=1),
    Column("money_wanted_named", numpy.int64, "1 where the crew key has a figure", "flag", width=1),
    Column("fleet_wanted", numpy.float64, "wear a year its routes' stock called for, by carrier good", "units", width=1),
    Column("fleet_wanted_named", numpy.int64, "1 where the carrier good was called for", "flag", width=1),
    Column("worn", numpy.float64, "carrier units its shipments wore, by carrier good", "units", width=1),
    Column("worn_named", numpy.int64, "1 where the carrier good was worn", "flag", width=1),
    Column("rent", numpy.float64, "what it paid each merchant it hired carriers from, by that merchant's row", "money", width=1),
    Column("cash_after", numpy.float64, "its purse once the year's postings are made", "money"),
])
DispatchMerchantResults = MERCHANT_RESULTS.make_type(__name__)


def new(spec, table_type, rows: int, **widths):
    """An all-zero table of `rows` rows in use, the widths named by column."""
    return spec.new_table(table_type, max(rows, 1), rows, widths=widths)
