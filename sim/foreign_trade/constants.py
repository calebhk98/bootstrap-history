"""Foreign trade's declared numbers and the names of its books' fields."""
from sim.constants import declare

OPENING_CARRIERS_PER_ROUTE = declare(
    "OPENING_CARRIERS_PER_ROUTE", 10.0, kind="temporary_heuristic",
    unit="hull-equivalents on a route at the start", source=None, confidence="D",
    why="Merchants already ply a route when the game opens, so lift is not zero; the number is an "
        "initial condition not yet derived from the route's known traffic.")

FOREIGN_OPENING_IN_BALANCE = declare(
    "FOREIGN_OPENING_IN_BALANCE", 1.0, kind="temporary_heuristic",
    unit="foreign capacity over foreign demand for a good it can make",
    source=None, confidence="D",
    why="A foreign economy's made or grown goods open with its capacity "
        "equal to its households' demand, so its own market is in balance "
        "until trade moves it; its land, labour and trades do not yet cap "
        "that output (Complaints/109).")

FOREIGN_OUTPUT_PER_POPULATION_SHARE = declare(
    "FOREIGN_OUTPUT_PER_POPULATION_SHARE", 1.0, kind="temporary_heuristic",
    unit="a partner's output of a good it can make over the stated national output, per unit of population ratio",
    source=None, confidence="D",
    why="A good bought only as an input has no partner demand figure to size its supply, so a partner that "
        "holds every technique, input and deposit for it makes the stated national output scaled one-for-one "
        "by its population over the one the table is stated for, until an industrial output model sizes it.")

TRADE_YEARS_KEPT = 3   # years of imports and exports the value book keeps

# a partner's ledger
LEDGER_FIELDS = ("goods_in_value", "goods_out_value", "home_coin_units", "partner_coin_units",
                 "lift_tonnes_per_year", "lift_used_in", "lift_used_out", "lift_unmet",
                 "lift_year", "coin_carriage_units")

# an actor-trade tally, by partner and material
LANDED = "landed_tonnes"   # carried into the home market
TAKEN = "taken_tonnes"     # carried out of the home market
SOLD = "sold_tonnes"       # carried to the partner
BOUGHT = "bought_tonnes"   # carried from the partner
LANDED_COST = "landed_cost_money"   # what the tonnes carried to the partner cost the carriers there: purchase, carriage, dues, margin

# a trader's cargo leg
LANDING, TAKING, THROUGH = "in", "out", "through"
SETTLEMENT = "edge:market settlement"
