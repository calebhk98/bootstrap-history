"""What the freight module fixes: the carriage modes it names and the carrier a domestic haul is priced with."""
from sim.constants import declare

CARAVAN_STRING_SIZE = declare(
    "CARAVAN_STRING_SIZE", 10.0, kind="engineering_estimate",
    unit="pack mules per handler",
    source="Pack trains in the ancient and medieval world went in strings "
           "of a few to a few dozen animals under a small crew.",
    confidence="C",
    why="One handler's day is spread over the string's cargo, which sets "
        "the driver hours per tonne-km of a caravan.")

LAND_FREIGHT_TEAM_SIZE = declare(
    "LAND_FREIGHT_TEAM_SIZE", 2.0, kind="engineering_estimate",
    unit="draught oxen",
    source="sim/geography/transport.py's own headline example throughout that module's docstring, __main__ block and "
           "test suite (draught_freight_physical_inputs(OX, 2, CART, ...)); reused here rather than a second, unrelated "
           "team size invented for ordinary market freight.",
    confidence="C",
    why="How many oxen pull the cart that ordinary market freight is priced with. Paired with DIRT_TRACK, not "
        "PAVED_ROAD or MUD, because transport.py's own docstring calls dirt track 'the ordinary, unimproved-road case "
        "most freight in this period actually moved over': the middle case, not either extreme.")

SEA_CREW_WAGE_TRADE = "sailor"
SEA_MODE = "sail"
RAIL_MODE = "rail"
CANAL_MODE = "canal"
DOMESTIC_CART_MODE = "cart"
# Vehicles and hulls are priced as their timber (their iron fittings are left out).
FREIGHT_VEHICLE_MATERIAL = "wood_kg"
# The existing book price and wage that turn transport.py's physical quantities (feed kilograms, driver hours) into
# money. Plain strings: which existing number to read, not a number. Wheat is dearer per kilogram than real fodder, so
# the feed cost is an upper bound.
FREIGHT_FEED_PRICE_MATERIAL = "wheat_kg"
FREIGHT_DRIVER_WAGE_TRADE = "labourer"
# Hauled materials whose routes are kept, before the oldest are dropped.
MATERIAL_ROUTES_KEPT = 512

LIVING_STOCK_CARGO = "living_stock"
GOODS_CARGO = "goods"
