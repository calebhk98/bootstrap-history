"""The numbers the materials module declares: market reach of the tracked commodities, what a standing installation draws,
electricity loads and the throttle floor (each with its provenance, sim/constants.py)."""


from sim.constants import declare


_MARKET_SHARE_WHY = (
    "What fraction of the empire's whole annual national output of "
    "this material an ordinary buyer with no special standing can "
    "actually reach, before patronage multipliers (see "
    "_material_market_tonnes) apply. Bulk, transportability and how "
    "concentrated ownership of the resource is (imperial mints and "
    "metalla versus an ordinary quarry) all matter physically, but no "
    "attested Roman market-share figure exists for any of these "
    "materials; each is reasoned by hand from those physical "
    "properties, not measured.")

MARKET_SHARE_CHARCOAL = declare(
    "MARKET_SHARE_CHARCOAL", 0.002, kind="temporary_heuristic",
    unit="fraction of national output", source=None,
    confidence="D",
    why=_MARKET_SHARE_WHY + " Charcoal specifically is bulky and "
        "crumbles when carted, so it is treated as almost entirely "
        "a local commodity regardless of total empire-wide output.")

MARKET_SHARE_IRON = declare(
    "MARKET_SHARE_IRON", 0.03, kind="temporary_heuristic",
    unit="fraction of national output", source=None,
    confidence="D", why=_MARKET_SHARE_WHY)

MARKET_SHARE_COPPER = declare(
    "MARKET_SHARE_COPPER", 0.03, kind="temporary_heuristic",
    unit="fraction of national output", source=None,
    confidence="D", why=_MARKET_SHARE_WHY)

MARKET_SHARE_LEAD = declare(
    "MARKET_SHARE_LEAD", 0.03, kind="temporary_heuristic",
    unit="fraction of national output", source=None,
    confidence="D", why=_MARKET_SHARE_WHY)

MARKET_SHARE_TIN = declare(
    "MARKET_SHARE_TIN", 0.05, kind="temporary_heuristic",
    unit="fraction of national output", source=None,
    confidence="D", why=_MARKET_SHARE_WHY)

MARKET_SHARE_SILVER = declare(
    "MARKET_SHARE_SILVER", 0.01, kind="temporary_heuristic",
    unit="fraction of national output", source=None,
    confidence="D",
    why=_MARKET_SHARE_WHY + " Held low specifically because "
        "silver mining was heavily imperial-mint property, which "
        "MARKET_SHARE_GOLD's own sourced figure also reflects.")

MARKET_SHARE_COAL = declare(
    "MARKET_SHARE_COAL", 0.50, kind="temporary_heuristic",
    unit="fraction of national output", source=None,
    confidence="D",
    why=_MARKET_SHARE_WHY + " Held high specifically because coal "
        "was barely used by anyone in this period, so almost all "
        "of the (small) national output is available to a buyer.")

MARKET_SHARE_SALTPETRE = declare(
    "MARKET_SHARE_SALTPETRE", 0.0, kind="temporary_heuristic",
    unit="fraction of national output", source=None,
    confidence="D",
    why=_MARKET_SHARE_WHY + " Zero specifically because there is "
        "no open saltpetre market at all in this period; it is "
        "made in nitre beds, not bought (see the resources module's `LayNitreBeds`).")

MARKET_SHARE_GOLD = declare(
    "MARKET_SHARE_GOLD", 0.01, kind="temporary_heuristic",
    unit="fraction of national output",
    source="commodities.json's own gold entry (market_share), "
           "already reasoned there against imperial-mint scarcity - "
           "reused here rather than re-guessed so the two files "
           "agree on how tightly a private buyer can reach the "
           "metalla's gold.",
    confidence="C", why=_MARKET_SHARE_WHY)

MARKET_SHARE = {
    'charcoal': MARKET_SHARE_CHARCOAL,
    'iron': MARKET_SHARE_IRON,
    'copper': MARKET_SHARE_COPPER,
    'lead': MARKET_SHARE_LEAD,
    'tin': MARKET_SHARE_TIN,
    'silver': MARKET_SHARE_SILVER,
    'coal': MARKET_SHARE_COAL,
    'saltpetre': MARKET_SHARE_SALTPETRE,
    'gold': MARKET_SHARE_GOLD,
}

GENERIC_MARKET_SHARE_LEDGER_FALLBACK = declare(
    "GENERIC_MARKET_SHARE_LEDGER_FALLBACK", 0.03, kind="temporary_heuristic",
    unit="fraction of national output", source=None, confidence="D",
    why="Fallback market share for a curated commodities.json commodity "
        "that names no market_share field of its own - a middling, "
        "unremarkable buyable fraction picked so a missing field does "
        "not silently become 'unbuyable' or 'unlimited'.")

COKE_PER_CHARCOAL = declare(
    "COKE_PER_CHARCOAL", 0.85, kind="engineering_estimate",
    unit="kg coal-equivalent demand per kg of charcoal it replaces",
    source="Blast-furnace fuel consumption ratios: roughly 3 kg "
           "charcoal per kg of iron by the charcoal route, versus "
           "roughly 1.6 kg coke (itself roughly 1.6 kg of coal) per kg "
           "of iron by the coke route - see the comment above for the "
           "arithmetic (2.56 kg coal / 3 kg charcoal is approximately "
           "0.85).",
    confidence="C",
    why="Converts a node's charcoal demand into the equivalent coal "
        "demand when coke is the chosen fuel - the actual substitution "
        "that decided whether an industrialising civilisation is bound "
        "by grown fuel or dug fuel.")

STANDING_MATERIAL_DRAW_SHARE = declare(
    "STANDING_MATERIAL_DRAW_SHARE", 0.5, kind="temporary_heuristic",
    unit="fraction of a node's build-time material draw rate, per year "
         "of standing operation", source=None, confidence="D",
    why="A finished, running installation - a furnace, a workshop - "
        "goes on consuming its listed material every year it operates, "
        "not only while being built (see the comment above: 'a furnace "
        "does not eat charcoal only while it is being built'). This is "
        "the ongoing rate as a fraction of the build-time rate, reused "
        "identically for electrical demand in _electricity_demand_kw() "
        "and _node_annual_tonnes() below. The DIRECTION is a real "
        "physical claim (standing operation consumes fuel/electricity "
        "continuously); the specific half-rate is an invented "
        "placeholder - a real figure needs a per-process duty cycle or "
        "throughput figure this tree does not carry.")

FIREWOOD_PER_CHARCOAL_MASS_RATIO = declare(
    "FIREWOOD_PER_CHARCOAL_MASS_RATIO", 4.0, kind="engineering_estimate",
    unit="kg raw firewood per kg-equivalent of charcoal (dimensionless)",
    source="Traditional charcoal-burning loses most of the wood's mass "
           "as volatiles and water during carbonisation; a roughly "
           "four-to-one wood-to-charcoal mass ratio is the commonly "
           "cited order of magnitude for earth-kiln and pit methods.",
    confidence="C",
    why="A hectare of coppice yields several times more mass as raw, "
        "unconverted firewood (the 'forest4' tag, firewood_kg's supply) "
        "than it does as charcoal (the 'forest1' tag) from the SAME "
        "wood, because charcoal-making itself consumes most of the "
        "mass. This is the ratio between those two yields.")

MARKET_STANDING_SHARE_CEILING = declare(
    "MARKET_STANDING_SHARE_CEILING", 0.60, kind="temporary_heuristic",
    unit="fraction of national output (maximum, any buyer)",
    source=None, confidence="D",
    why="However much standing multiplies a buyer's reach, nobody but "
        "the state itself commands the whole national market for a "
        "material - this caps even an imperial patron's buyer well "
        "short of monopolising it. The cap's own level is a plausible "
        "round number, not derived from an attested ceiling.")

SALTPETRE_TRADE_ROUTE_TONNES_PER_YR = declare(
    "SALTPETRE_TRADE_ROUTE_TONNES_PER_YR", 60.0, kind="temporary_heuristic",
    unit="tonnes/year", source=
    "the geography data's Bengal saltpetre sea-route entry, reused here as "
    "'the single most useful thing in the geography file' per the "
    "comment above - the ROUTE'S existence is a geography fact, but "
    "this file has no independent attested annual tonnage for it.",
    confidence="D",
    why="How much extra saltpetre a year an extended trade route to "
        "Bengal makes available, on top of the ordinary market. The "
        "route is real; the specific tonnage is an invented, plausible "
        "figure standing in for an actual historical trade-volume "
        "record.")

# the tracked commodities: material key -> (commodity, supply-pool tag); every other key is its own pool
MATERIAL_CHECKS = {
    "charcoal_kg": ("charcoal", "forest1"),
    "firewood_kg": ("charcoal", "forest4"),
    "iron_bar_kg": ("iron", "mine:iron"),
    "iron_ore_kg": ("iron", "mine:iron"),
    "coal_kg":     ("coal", "mine:coal"),
    "copper_kg":       ("copper", "mine:copper"),
    "copper_wire_kg":  ("copper", "mine:copper"),
    "wire_drawn_kg":   ("copper", "mine:copper"),
    "lead_kg":     ("lead", "mine:lead"),
    "tin_kg":      ("tin", "mine:tin"),
    "silver_kg":   ("silver", "mine:silver"),
    "gold_kg":     ("gold", "mine:gold"),
    "nitre_kg":    ("saltpetre", "nitre"),
}

LAB_SCALE_SUFFIX = "_g"      # a key in grams is a bench quantity: met from stock or bought outright, never throttled
NON_PHYSICAL_CAPACITY_KEYS = frozenset(("scholar_hours", "machinist_hours", "patronage"))

HOURS_PER_YEAR = declare(
    "HOURS_PER_YEAR", 8760.0, kind="physical_constant",
    unit="hours/year (365-day year)", source="365 days x 24 hours.",
    confidence="A",
    why="Converts an average continuous kilowatt draw into an annual "
        "energy total (and back), the same role HOURS_PER_DAY plays in "
        "sim/world/agriculture.py. Deliberately the plain 365-day "
        "figure, not 365.25: this file has no use for leap-year "
        "precision at kilowatt-scale estimates.")

ALUMINIUM_KWH_PER_KG = declare(
    "ALUMINIUM_KWH_PER_KG", 15.0, kind="engineering_estimate",
    unit="kWh/kg aluminium",
    source="Hall-Heroult aluminium electrolysis: 13-17 kWh/kg is the "
           "historical-to-modern range; taken at the midpoint.",
    confidence="B",
    why="Specific energy of electrolytic aluminium production, applied "
        "to electrolysis_industrial's own bauxite draw via "
        "BAUXITE_PER_ALUMINIUM_KG to give electrical demand per kg of "
        "bauxite, the tree's own material key for this node.")

BAUXITE_PER_ALUMINIUM_KG = declare(
    "BAUXITE_PER_ALUMINIUM_KG", 4.5, kind="engineering_estimate",
    unit="kg bauxite per kg aluminium",
    source="Bayer process bauxite yield is roughly 4-5 t bauxite per t "
           "aluminium, varying with ore grade and process losses; "
           "taken at the midpoint.",
    confidence="B",
    why="Converts aluminium's own specific energy (ALUMINIUM_KWH_PER_KG) "
        "into energy per kg of BAUXITE, since electrolysis_industrial's "
        "own `mat` dict draws bauxite_kg, not an aluminium mass the "
        "tree never states.")

GENERIC_ELECTRIC_LOAD_KW = declare(
    "GENERIC_ELECTRIC_LOAD_KW", 15.0, kind="temporary_heuristic",
    unit="kW", source=None, confidence="D",
    why="Flat electrical demand assumed for any node gated on "
        "generated electricity that this file cannot characterise "
        "individually (see ELECTRICAL_PROCESSES for the two that are). "
        "Deliberately modest - the same order as cap_power_electric's "
        "own anchor, a full order of magnitude under the two curated "
        "heavy loads - so an uncharacterised node's demand is present "
        "but never dominant. Not measured for any specific process.")

RESOURCE_THROTTLE_FLOOR = declare(
    "RESOURCE_THROTTLE_FLOOR", 0.05, kind="temporary_heuristic",
    unit="fraction of full pace (minimum)", source=None,
    confidence="D",
    why="A material or electricity shortfall slows work rather than "
        "stopping it dead - a shortage is a real cost, not a wall a "
        "player cannot work around at all. The floor's own level (work "
        "always creeps forward at at least 5% pace) is a game-design "
        "choice, not derived from any real bound on how slow "
        "under-resourced work can go.")

MATERIAL_PRICE_DEMAND_SHARE_CAP = declare(
    "MATERIAL_PRICE_DEMAND_SHARE_CAP", 1.5, kind="temporary_heuristic",
    unit="dimensionless (demand / available supply, maximum)",
    source=None, confidence="D",
    why="Ceiling on how far demand-over-supply can push the price "
        "pressure curve below, so a wildly oversubscribed material "
        "does not blow the price multiplier up without bound. A "
        "defensive cap, not a market-clearing figure.")

MATERIAL_PRICE_PRESSURE_SCALE = declare(
    "MATERIAL_PRICE_PRESSURE_SCALE", 0.9, kind="temporary_heuristic",
    unit="dimensionless coefficient on (demand share)^2", source=None,
    confidence="D",
    why="How hard buying near or above the market's available supply "
        "of a material pushes its price up - a quadratic curve, per "
        "this method's own docstring, 'negligible at a fifth of the "
        "ceiling, roughly double at the whole of it'. The quadratic "
        "SHAPE is a real modelling choice (price pressure should "
        "accelerate near scarcity); the coefficient is tuned to hit "
        "that 'roughly double' target, not derived from an observed "
        "price-response curve for any real material market.")
