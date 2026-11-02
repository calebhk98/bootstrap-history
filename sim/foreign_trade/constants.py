"""Foreign trade's declared numbers and the names of its books' fields."""
from sim.constants import declare

OPENING_CARRIERS_PER_ROUTE = declare(
    "OPENING_CARRIERS_PER_ROUTE", 10.0, kind="temporary_heuristic",
    unit="hull-equivalents on a route at the start", source=None, confidence="D",
    why="Merchants already ply a route when the game opens, so lift is not zero; the number is an "
        "initial condition not yet derived from the route's known traffic.")

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
